from typing import Iterable, TypeVar, Generic, Sequence, cast, Any

from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.threading_exception import ThreadingException
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.parallel.pipeline.p_iterable import PIterable
from runtime.threading.core.parallel.pipeline.producer_consumer_queue import ProducerConsumerQueue
from runtime.threading.core.parallel.for_each import for_each

T = TypeVar("T")

DistributionAlreadyStartedError = ThreadingException("Distribution has already begun")

class Distributor(Generic[T]):
    __slots__ = ["__queue_in", "__queues_out", "__sealed"]

    def __init__(self, items: Iterable[T]):
        self.__queue_in: PIterable[T] = items if isinstance(items, PIterable) else ProducerConsumerQueue[T](items).get_iterator() # put items in a ProducerConsumerQueue, if items is not a PIterable instance
        self.__queues_out: list[ProducerConsumerQueue[T]] = []
        self.__sealed = False


    def start(self, interrupt: Interrupt | None = None) -> None:
        """Seals distributor

        Args:
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.
        """
        if self.__sealed:
            raise DistributionAlreadyStartedError

        self.__sealed = True

        def distribute(task: Task[None], item: T) -> None:
            task.interrupt.raise_if_signaled()
            for queue in self.__queues_out:
                queue.put(item)

        def success(task: Task[None], tasks: Sequence[Task[T]]):
            for queue in self.__queues_out:
                queue.complete()

        def cancel(task: Task[None], tasks: Sequence[Task[Any]]):
            exceptions: dict[int, Exception] = {}
            for canceled_task in [ task for task in tasks if task.is_canceled ]:
                exception = cast(InterruptException, canceled_task.exception)
                exceptions[exception.interrupt.signal_id or 0] = exception

            if len(exceptions) == 1:
                exception = exceptions[0]
            else:
                exception = AggregateException(tuple(exceptions.values())) # pragma: no cover -- this should never happen under normal circumstances

            for queue in self.__queues_out:
                queue.fail(cast(Exception, exception))

        def fail(task: Task[None], tasks: Iterable[Task[Any]]): # pragma: no cover -- it's impossible to trigger an exception to test this
            exception = AggregateException(tuple(cast(Exception, task.exception) for task in tasks if task.is_failed ))

            for queue in self.__queues_out:
                queue.fail(exception)

        tasks = [ for_each(self.__queue_in, interrupt = interrupt).do(distribute) ]


        Task.with_all(tasks, options=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE).run(success)
        Task.with_any(tasks, options=ContinuationOptions.ON_FAILED | ContinuationOptions.INLINE).run(fail)
        Task.with_any(tasks, options=ContinuationOptions.ON_CANCELED | ContinuationOptions.INLINE).run(cancel)

    def take(self) -> PIterable[T]:
        """Adds a consumer to the distributor instance

        Returns:
            Iterable[T]: An iterable
        """
        if self.__sealed:
            raise DistributionAlreadyStartedError

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
