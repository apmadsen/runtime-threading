from typing import Iterable, TypeVar, Generic, Sequence, cast, Any

from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.tasks.task_interrupt_exception import TaskInterruptException
from runtime.threading.core.tasks.threading_exception import ThreadingException
from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.parallel.p_iterable import PIterable
from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue, ProducerConsumerQueueIterator
from runtime.threading.core.parallel.for_each import for_each

T = TypeVar("T")

class Distributor(Generic[T]):
    __slots__ = ["__queue_in", "__queues_out", "__sealed"]

    def __init__(self, items: Iterable[T]):
        self.__queue_in: PIterable[T] = items if isinstance(items, ProducerConsumerQueueIterator) else ProducerConsumerQueue[T](items).get_iterator() # put items in a ProducerConsumerQueue, if items is not a ProducerConsumerQueueIterator instance
        self.__queues_out: list[ProducerConsumerQueue[T]] = []
        self.__sealed = False


    def start(self, interrupt: Interrupt) -> None:
        """Seals distributor

        Args:
            interrupt (Interrupt, optional): The Interrupt. Defaults to Interrupt.none().
        """
        if self.__sealed:
            raise ThreadingException("Distribution has already begun")

        self.__sealed = True

        def distribute(task: Task[None], item: T) -> None:
            task.interrupt.raise_if_signaled()
            for queue in self.__queues_out:
                queue.put(item)

        def success(task: Task[None], tasks: Iterable[Task[T]]):
            for queue in self.__queues_out:
                queue.complete()

        def cancel(task: Task[None], tasks: Iterable[Task[Any]]):
            for queue in self.__queues_out:
                queue.fail(TaskInterruptException(interrupt))

        def fail(task: Task[None], tasks: Iterable[Task[Any]]):
            exceptions: Sequence[Exception] = []
            for failed_task in [ task for task in tasks if task.is_failed ]:
                exception = cast(Exception, failed_task.exception)
                if isinstance(exception, AggregateException):
                    exception = exception.flatten()

                exceptions.append(exception)
            for queue in self.__queues_out:
                queue.fail(AggregateException(exceptions))

        tasks = [ for_each(self.__queue_in, interrupt = interrupt).do(distribute) ]

        Task.with_all(tasks, options=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE).then(success)
        Task.with_any(tasks, options=ContinuationOptions.ON_FAILED | ContinuationOptions.INLINE).then(fail)
        Task.with_any(tasks, options=ContinuationOptions.ON_CANCELED | ContinuationOptions.INLINE).then(cancel)

    def take(self) -> PIterable[T]:
        """Adds a consumer to the distributor instance

        Returns:
            Iterable[T]: An iterable
        """
        if self.__sealed:
            raise ThreadingException("Distribution has already begun")

        queue = ProducerConsumerQueue[T]()
        self.__queues_out.append(queue)
        return queue.get_iterator()

def distribute(items: Iterable[T]) -> Distributor[T]:
    """Distributes the source items into several consumers.

    Args:
        items (Iterable[T]): The source items

    Returns:
        Distributor[T]: A Distributor instance
    """
    return Distributor[T](items)
