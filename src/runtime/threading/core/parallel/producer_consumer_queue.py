from typing import TypeVar, Generic, Iterable, Any, cast, overload
from time import time

from runtime.threading.core.event import Event
from runtime.threading.core.auto_clear_event import AutoClearEvent
from runtime.threading.core.concurrent.queue import Queue
from runtime.threading.core.parallel.parallel_exception import ParallelException
from runtime.threading.core.parallel.pipeline.p_iterable import PIterable
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.interrupt import Interrupt

QueueCompletedError = ParallelException("ProducerConsumerQueue is completed")
QueueLinkedToAnotherQueueError = ParallelException("ProducerConsumerQueue is linked to the output of a ProducerConsumerQueueIterator, and therefore cannot be completed manually")

T = TypeVar('T')

class ProducerConsumerQueue(Generic[T]):
    """The ProducerConsumerQueue class is an implemention of the producer/consumer pattern,
    providing a queue on which work can be added and consumed asynchronously on different threads.

    The workflow is as follows: The producer thread is responsible for putting items into the queue, and subsequently calline `complete()` when done, while the consumer merely
    consumes the items by either calling `try_take()` repeatedly or iterating over the iterator created by calling `get_iterator()`.
    """
    __slots__ = [ "__queue", "__notify_event", "__is_complete", "__is_failed", "__fail", "__is_async" ]

    @overload
    def __init__(self) -> None:
        """Creates a new empty ProducerConsumerQueue.
        """
        ...
    @overload
    def __init__(self, data: Iterable[T]) -> None:
        """Creates a new ProducerConsumerQueue with existing work.

        Args:
            data (Iterable[T]): Any preexisting work to be added to the queue.
        """
        ...
    def __init__(self, data: Iterable[T] | None = None):
        self.__queue: Queue[T] = Queue()
        self.__notify_event = AutoClearEvent(purpose = "PRODUCER_CONSUMER_QUEUE_NOTIFY")
        self.__is_complete = False
        self.__is_failed = False
        self.__is_async = False
        self.__fail: Exception | None = None

        if data is not None:
            from runtime.threading.core.parallel.producer_consumer_queue_iterator import ProducerConsumerQueueIterator
            if isinstance(data, ProducerConsumerQueueIterator):
                self.__is_async = True

                def complete(task_in: Task[Any], task: Task[T]):
                    self.__is_complete = True
                    self.__notify_event.signal()

                self.put_many_async(cast(Iterable[T], data)).continue_with(ContinuationOptions.DEFAULT, complete)
            else:
                self.put_many(data)
                self.__is_complete = True
                self.__notify_event.signal()

    @property
    def is_complete(self) -> bool:
        """Indicates if the queue is complete.
        """
        return self.__is_complete

    @property
    def is_failed(self) -> bool:
        """Indicates if the queue is failed.
        """
        return self.__is_failed

    @property
    def is_async(self) -> bool:
        """Indicates if the queue is consuming from another `ProducerConsumerQueue`.
        """
        return self.__is_async

    @property
    def wait_event(self) -> Event:
        """The internal event, signaled when items are added.
        """
        return self.__notify_event


    def put(self, item: T) -> None:
        """Adds an item to the queue.

        Args:
            item (T): The item.
        """
        if self.__is_async:
            raise QueueLinkedToAnotherQueueError
        elif self.__is_complete:
            raise QueueCompletedError

        self.__queue.enqueue(item)
        self.__notify_event.signal()

    def put_many(self, items: Iterable[T]) -> None:
        """Adds multiple items to the queue.

        Args:
            items (Iterable[T]): The items.
        """
        if self.__is_async:
            raise QueueLinkedToAnotherQueueError
        elif self.__is_complete:
            raise QueueCompletedError

        for item in items:
            self.__queue.enqueue(item)
            self.__notify_event.signal()

    def put_many_async(self, items: Iterable[T]) -> Task[Any]:
        """Adds multiple items to the queue asynchronously (non-blocking).

        Args:
            items (Iterable[T]): The items
        """
        def async_fill(task: Task[Any]):
            for item in items:
                self.__queue.enqueue(item)
                self.__notify_event.signal()
            self.__notify_event.signal()

        return Task.run(async_fill)

    def take(
        self,
        timeout: float | None = 0, /,
        interrupt: Interrupt | None = None
    ) -> T:
        """Tries to take an item from the queue. If a timeout is specified, call will block until an item can be produced
        or timeout is met. Will raise a `TimeoutError` exception if timeout is not None and timeout exceeded.

        Args:
            timeout (float, optional): The timeout. Defaults to 0.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Raises:
            TimeoutError: Raises a TimeoutError if operation times out.

        Returns:
            T: Returns the item produced from the queue.
        """
        was_empty = False
        t_start = time()
        initial_timeout = timeout

        while True:
            timeout = max(0, timeout-(time()-t_start)) if timeout is not None else None
            try:
                if self.__is_failed:
                    raise cast(Exception, self.__fail)

                result = self.__queue.dequeue(timeout = timeout or 0, interrupt=interrupt)

                was_empty = False

                return result
            except TimeoutError:
                if self.is_complete:
                    # if queue was completed in another thread, it may not be empty at this point,
                    # so we need to run iteration one more time just to make sure
                    if not was_empty:
                        was_empty = True
                    else:
                        raise TimeoutError
                elif initial_timeout == 0 or not self.__notify_event.wait(timeout, interrupt):
                    raise TimeoutError
                elif interrupt is not None:
                    interrupt.raise_if_signaled() # pragma: no cover



    def try_take(
        self,
        timeout: float | None = 0, /,
        interrupt: Interrupt | None = None
    ) -> tuple[T | None, bool]:
        """Tries to take an item from the queue. If a timeout is specified, call will block until an item can be produced
        or timeout is met.

        Args:
            timeout (float, optional): The timeout. Defaults to 0.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Returns:
            tuple[T | None, bool]: The item and a boolean value indicating success of the take operation
        """
        try:
            return self.take(timeout, interrupt = interrupt), True
        except TimeoutError:
            return None, False


    def complete(self) -> None:
        """Marks the queue completed. The queue will not accept additional items afterwards.
        """
        with self.__queue.synchronization_lock:
            if self.__is_async:
                raise QueueLinkedToAnotherQueueError
            elif self.__is_complete:
                raise QueueCompletedError

            self.__is_complete = True
            self.__notify_event.signal()


    def fail(self, error: Exception) -> None:
        """Marks the queue failed with the specified exception. The queue will not accept additional items afterwards.

        Args:
            error (Exception): The exeception that caused the process to fail.

        Raises:
            QueueCompletedError: Raises an exception if queue is already completed.
        """
        if self.__is_async:
            raise QueueLinkedToAnotherQueueError

        with self.__queue.synchronization_lock:
            if self.__is_complete:
                raise QueueCompletedError

            self.fail_if_not_complete(error)

    def fail_if_not_complete(self, error: Exception) -> None:
        """If not completed, marks the queue failed. The queue will not accept additional items afterwards

        Args:
            error (Exception): The exeception that caused the process to fail.

        Raises:
            QueueLinkedToAnotherQueueError: Raises an exception if queue is async (eg. linked to the output of a ProducerConsumerQueueIterator).
        """
        if self.__is_async:
            raise QueueLinkedToAnotherQueueError

        with self.__queue.synchronization_lock:
            if not self.__is_complete:
                self.__fail = error
                self.__is_complete = True
                self.__is_failed = True
                self.__notify_event.signal()
            else:
                pass


    def get_iterator(self) -> PIterable[T]:
        """Returns a `ProducerConsumerQueueIterator[T]` used for blocking interruptable iteration.

        Returns:
            ProducerConsumerQueueIterator[T]: A ProducerConsumerQueueIterator instance
        """

        from runtime.threading.core.parallel.producer_consumer_queue_iterator import ProducerConsumerQueueIterator

        return ProducerConsumerQueueIterator[T](self)


