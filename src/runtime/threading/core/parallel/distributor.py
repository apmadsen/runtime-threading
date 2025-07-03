from typing import Iterable, TypeVar, Generic, Sequence, Any, cast, overload

from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.parallel.parallel_exception import ParallelException
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.parallel.pipeline.p_iterable import PIterable
from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue
from runtime.threading.core.parallel.for_each import for_each

T = TypeVar("T")

DistributionAlreadyStartedError = ParallelException("Distribution has already begun")

class Distributor(Generic[T]):
    """The Distributor class is used for processing a no. of items on multiple consumers simultaneously.
    The items aren't divided amongst the consumers, but duplicated thus enabling multiple consumers
    to process the same work.
    """
    __slots__ = [ "__scheduler", "__queue_in", "__queues_out", "__sealed" ]

    @overload
    def __init__(self, items: Iterable[T], /) -> None:
        """Creates a new Distributor instance.

        Args:
            items (Iterable[T]): The source items
        """
        ...
    @overload
    def __init__(self, items: Iterable[T], /, scheduler: TaskScheduler) -> None:
        """Creates a new Distributor instance.

        Args:
            items (Iterable[T]): The source items
            scheduler (TaskScheduler): The scheduler onto which tasks are scheduled.
        """
        ...
    def __init__(self, items: Iterable[T], /, scheduler: TaskScheduler | None = None):
        self.__queue_in: PIterable[T] = items if isinstance(items, PIterable) else ProducerConsumerQueue[T](items).get_iterator() # put items in a ProducerConsumerQueue, if items is not a PIterable instance
        self.__queues_out: list[ProducerConsumerQueue[T]] = []
        self.__sealed = False
        self.__scheduler = scheduler


    def start(self, interrupt: Interrupt | None = None) -> Task[None]:
        """Seals distributor and begins distributing.

        Args:
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Returns:
            Task[None]: Returns an awaitable task.
        """
        if self.__sealed:
            raise DistributionAlreadyStartedError

        self.__sealed = True

        def distribute(task: Task[None], item: T) -> None:
            task.interrupt.raise_if_signaled()
            for queue in self.__queues_out:
                queue.put(item)

        def succeeded(task: Task[None], tasks: Sequence[Task[T]]):
            for queue in self.__queues_out:
                queue.complete()

        def interrupted(task: Task[None], tasks: Sequence[Task[Any]]):
            exceptions: dict[int, Exception] = {}
            for interrupteded_task in [ task for task in tasks if task.is_interrupted ]:
                exception = cast(InterruptException, interrupteded_task.exception)
                exceptions[exception.interrupt.signal_id or 0] = exception

            if len(exceptions) == 1:
                exception = exceptions[0]
            else:
                exception = AggregateException(tuple(exceptions.values())) # pragma: no cover -- this should never happen under normal circumstances

            for queue in self.__queues_out:
                queue.fail(cast(Exception, exception))

        def failed(task: Task[None], tasks: Iterable[Task[Any]]): # pragma: no cover -- it's impossible to trigger an exception to test this
            exception = AggregateException(tuple(cast(Exception, task.exception) for task in tasks if task.is_failed ))

            for queue in self.__queues_out:
                queue.fail(exception)

        tasks = [ for_each(self.__queue_in, interrupt = interrupt, scheduler = self.__scheduler).do(distribute) ]

        Task.with_all(tasks, options=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE).run(succeeded)
        Task.with_any(tasks, options=ContinuationOptions.ON_FAILED | ContinuationOptions.INLINE).run(failed)
        Task.with_any(tasks, options=ContinuationOptions.ON_INTERRUPTED | ContinuationOptions.INLINE).run(interrupted)
        return Task.with_any(tasks).plan()

    def take(self) -> PIterable[T]:
        """Adds a consumer to the distributor instance. Note that any work already done by other consumers,
        will be lost at this point, so it's better to add all consumers before adding any work.

        Returns:
            PIterable[T]: An iterable
        """
        if self.__sealed:
            raise DistributionAlreadyStartedError

        queue = ProducerConsumerQueue[T]()
        self.__queues_out.append(queue)
        return queue.get_iterator()

@overload
def distribute(items: Iterable[T], /) -> Distributor[T]:
    """Distributes the source items into several consumers.

    Args:
        items (Iterable[T]): The source items

    Returns:
        Distributor[T]: A Distributor instance
    """
    ...
@overload
def distribute(items: Iterable[T], /, scheduler: TaskScheduler ) -> Distributor[T]:
    """Distributes the source items into several consumers.

    Args:
        items (Iterable[T]): The source items
        scheduler (TaskScheduler): The scheduler onto which tasks are scheduled.

    Returns:
        Distributor[T]: A Distributor instance
    """
    ...
def distribute(items: Iterable[T], /, scheduler: TaskScheduler | None = None) -> Distributor[T]:
    return Distributor[T](items)
