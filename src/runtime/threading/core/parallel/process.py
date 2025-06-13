from typing import Sequence, Iterable, Callable, TypeVar, Concatenate, ParamSpec, Any, Generic, cast, overload

from runtime.threading.core.tasks.interrupt_signal import InterruptSignal
from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.tasks.task_interrupt_exception import TaskInterruptException
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.parallel.p_iterable import PIterable
from runtime.threading.core.parallel.parallel_context import ParallelContext
from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue, ProducerConsumerQueueIterator
from runtime.threading.core.tasks.helpers import get_function_name

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")
P = ParamSpec("P")

class ProcessProto(Generic[Tin]):
    __slots__ = [ "__items", "__task_name", "__parallelism", "__interrupt", "__scheduler" ]

    def __init__(
        self,
        items: Iterable[Tin],
        task_name: str | None = None,
        parallelism: int | None = None,
        interrupt: Interrupt = Interrupt.none(),
        scheduler: TaskScheduler | None = None
    ):
        self.__task_name = task_name
        self.__items = items
        self.__parallelism = parallelism
        self.__interrupt = interrupt
        self.__scheduler = scheduler

    @overload
    def do(
        self,
        fn: Callable[Concatenate[Task[Any], Tin, P], Iterable[Tout]], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> PIterable[Tout]:
        ...
    @overload
    def do(
        self,
        fn: Callable[Concatenate[Task[Any], Tin, P], Iterable[Tout]], /,
        output_queue: ProducerConsumerQueue[Tout],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[None]:
        ...
    def do(
        self,
        fn: Callable[Concatenate[Task[Any], Tin, P], Iterable[Tout]], /,
        output_queue: ProducerConsumerQueue[Tout] | None = None,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> PIterable[Tout] | Task[None]:

        pc = ParallelContext.current()
        scheduler = self.__scheduler or TaskScheduler.current() if pc == ParallelContext.root() else pc.scheduler
        signal = InterruptSignal(self.__interrupt, pc.interrupt)
        interrupt = signal.interrupt
        parallelism = max(self.__parallelism or 0, pc.max_parallelism)

        queue_in = self.__items if isinstance(self.__items, ProducerConsumerQueueIterator) else ProducerConsumerQueue[Tin](self.__items).get_iterator() # put items in a ProducerConsumerQueue, if items is not a ProducerConsumerQueueIterator instance
        queue_out = output_queue or ProducerConsumerQueue[Tout]()

        def process(task: Task[None], queue_in: Iterable[Tin], queue_out: ProducerConsumerQueue[Tout]) -> None:
            for item in queue_in:
                queue_out.put_many(fn(task, item, *args, **kwargs))

        tasks = [
            Task.create(
                name = self.__task_name or get_function_name(fn) or None,
                scheduler = scheduler,
                interrupt = interrupt
            ).run(
                process,
                queue_in,
                queue_out
            )
            for _ in range(parallelism)
        ]

        def success(task: Task[Any], tasks: Iterable[Task[Any]]):
            if not output_queue:
                queue_out.complete()

        def cancel(task: Task[Any], tasks: Iterable[Task[Any]]):
            queue_out.fail(TaskInterruptException(interrupt))

        def fail(task: Task[Any], tasks: Iterable[Task[Any]]):
            exceptions: Sequence[Exception] = []
            for failed_task in [ task for task in tasks if task.is_failed ]:
                exception = cast(Exception, failed_task.exception)
                if isinstance(exception, AggregateException):
                    exception = exception.flatten()

                exceptions.append(exception)
            queue_out.fail(AggregateException(exceptions))


        task_success = Task.with_all(tasks, options=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE).then(success)
        task_canceled = Task.with_any(tasks, options=ContinuationOptions.ON_CANCELED | ContinuationOptions.INLINE).then(cancel)
        task_failed = Task.with_any(tasks, options=ContinuationOptions.ON_FAILED | ContinuationOptions.INLINE).then(fail)

        if not output_queue:
            return queue_out.get_iterator()
        else:
            return Task.with_any([task_success, task_canceled, task_failed]).task()

def process(
    items: Iterable[Tin], /,
    task_name: str | None = None,
    parallelism: int | None = None,
    interrupt: Interrupt = Interrupt.none(),
    scheduler: TaskScheduler | None = None,
) -> ProcessProto[Tin]:

    return ProcessProto(
        items,
        task_name,
        parallelism,
        interrupt,
        scheduler
    )
