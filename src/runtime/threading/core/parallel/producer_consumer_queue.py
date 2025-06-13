from typing import TypeVar, Generic, Iterable, Any, cast

from runtime.threading.core.tasks.auto_clear_event import AutoClearEvent as Event
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.parallel.parallel_exception import ParallelException
from runtime.threading.core.parallel.p_iterable import PIterable, PIterator
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.concurrent.queue import Queue

LINKED_TO_OUTPUT_EXCEPTION = ParallelException("ProducerConsumerQueue is linked to the output of a ProducerConsumerQueueIterator, and therefore cannot be completed manually")
T = TypeVar('T')

class ProducerConsumerQueue(Generic[T]):
    """A queue for implementing the producer/consumer pattern

    Args:
        Generic (type): The input type

    """
    __slots__ = ["__queue", "__notify_event", "__is_complete", "__is_failed", "__fail", "__is_async"]

    def __init__(self, data: Iterable[T] | None = None):
        """Creates a new ProducerConsumerQueue
        """
        self.__queue: Queue[T] = Queue()
        self.__notify_event = Event()
        self.__is_complete = False
        self.__is_failed = False
        self.__is_async = False
        self.__fail: Exception | None = None

        if data != None:
            if isinstance(data, ProducerConsumerQueueIterator):
                self.__is_async = True

                def complete(task_in: Task[Any], task: Task[T]):
                    self.__is_complete = True
                    self.__notify_event.set()

                self.put_many_async(cast(Iterable[T], data)).continue_with(ContinuationOptions.DEFAULT, complete)
            else:
                if data:
                    self.put_many(data)
                self.__is_complete = True
                self.__notify_event.set()

    @property
    def is_complete(self) -> bool:
        """Indicates if the queue is complete
        """
        return self.__is_complete

    @property
    def is_failed(self) -> bool:
        """Indicates if the queue is failed
        """
        return self.__is_failed

    @property
    def is_async(self) -> bool:
        """Indicates if the queue is linked to the output of a ProducerConsumerQueueIterator
        """
        return self.__is_async

    @property
    def wait_event(self) -> Event:
        """The internal event, signaled when items are added
        """
        return self.__notify_event



    def put(self, item: T) -> None:
        """Puts an item into the queue

        Args:
            item (T): The item
        """
        if self.__is_async:
            raise LINKED_TO_OUTPUT_EXCEPTION
        elif self.__is_complete:
            raise ParallelException("ProducerConsumerQueue is complete")

        self.__queue.enqueue(item)
        self.__notify_event.set()

    def put_many(self, items: Iterable[T]) -> None:
        """Puts items into the queue

        Args:
            items (Iterable[T]): The items
        """
        if self.__is_async:
            raise LINKED_TO_OUTPUT_EXCEPTION
        elif self.__is_complete:
            raise ParallelException("ProducerConsumerQueue is complete")

        for item in items:
            self.__queue.enqueue(item)
            self.__notify_event.set()

    def put_many_async(self, items: Iterable[T]) -> Task[Any]:
        """Puts items into the queue asynchronously

        Args:
            items (Iterable[T]): The items
        """
        def async_fill(task: Task[Any]):
            for item in items:
                self.__queue.enqueue(item)
                self.__notify_event.set()
            self.__notify_event.set()

        return Task.run(async_fill)

    def try_take(self, timeout: float | None = 0, interrupt: Interrupt = Interrupt.none()) -> tuple[T | None, bool]:
        """Tries to take an item from the queue.

        Args:
            timeout (float, optional): The timeout. Defaults to 0.
            interrupt (Interrupt, optional): The Interrupt. Defaults to Interrupt.none().

        Returns:
            tuple[T | None, bool]: The item and a boolean value indicating success of the take operation
        """
        was_empty = False
        while True:
            try:
                if self.__is_failed:
                    raise cast(Exception, self.__fail)

                result = self.__queue.dequeue(timeout=timeout or 0, interrupt=interrupt)

                was_empty = False
                return result, True
            except TimeoutError:
                if self.is_complete:
                    # if queue was completed in another thread, it may not be empty at this point,
                    # so we need to run iteration one more time
                    if not was_empty:
                        was_empty = True
                    else:
                        return None, False
                elif timeout == 0 or not Event.wait_any([self.__notify_event, interrupt.wait_event], timeout):
                    raise TimeoutError
                else:
                    interrupt.raise_if_signaled()



    def complete(self) -> None:
        """Marks the queue completed. The queue will not accept additional items afterwards
        """
        if self.__is_async:
            raise LINKED_TO_OUTPUT_EXCEPTION
        elif self.__is_complete:
            raise ParallelException("ProducerConsumerQueue is already completed")

        self.__is_complete = True
        self.__notify_event.set()


    def fail(self, error: Exception) -> None:
        """Marks the queue failed. The queue will not accept additional items afterwards

        Raises:
            Exception: Raises an exception if queue is already completed.
        """
        if self.__is_complete:
            raise ParallelException("ProducerConsumerQueue is already completed")

        self.fail_if_not_complete(error)

    def fail_if_not_complete(self, error: Exception) -> None:
        """Marks the queue failed. The queue will not accept additional items afterwards

        Raises:
            Exception: Raises an exception if queue is async (eg. linked to the output of a ProducerConsumerQueueIterator).
        """
        if self.__is_async:
            raise LINKED_TO_OUTPUT_EXCEPTION

        self.__fail = error
        self.__is_complete = True
        self.__is_failed = True
        self.__notify_event.set()


    def get_iterator(self) -> PIterable[T]:
        """Returns a blocking iterator for this ProducerConsumerQueue.

        Returns:
            Iterator[T]: A ProducerConsumerQueueIterator instance
        """
        return ProducerConsumerQueueIterator[T](self)


class ProducerConsumerQueueIterator(PIterable[T], PIterator[T]):
    __slots__ = ["__queue"]
    def __init__(self, queue: ProducerConsumerQueue[T]):
        self.__queue = queue

    def iter(self) -> PIterator[T]:
        return self

    def next(self, timeout: float | None = None, interrupt: Interrupt = Interrupt.none()) -> T:
        result, success = self.__queue.try_take(timeout, interrupt)
        if success:
            return result # type: ignore
        else:
            raise StopIteration
