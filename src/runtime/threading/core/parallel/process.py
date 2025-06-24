from typing import Sequence, Iterable, Callable, TypeVar, Concatenate, ParamSpec, Any, Generic, cast, overload

from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.parallel.pipeline.p_iterable import PIterable
from runtime.threading.core.parallel.pipeline.producer_consumer_queue import ProducerConsumerQueue, ProducerConsumerQueueIterator
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
        interrupt: Interrupt | None = None,
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

        parallelism = max(1, self.__parallelism or 2)

        queue_in = self.__items if isinstance(self.__items, ProducerConsumerQueueIterator) else ProducerConsumerQueue[Tin](self.__items).get_iterator() # put items in a ProducerConsumerQueue, if items is not a ProducerConsumerQueueIterator instance
        queue_out = output_queue or ProducerConsumerQueue[Tout]()

        def process(task: Task[None], queue_in: Iterable[Tin], queue_out: ProducerConsumerQueue[Tout]) -> None:
            for item in queue_in:
                task.interrupt.raise_if_signaled()
                queue_out.put_many(fn(task, item, *args, **kwargs))

        tasks = [
            Task.create(
                name = self.__task_name or get_function_name(fn) or None,
                scheduler = self.__scheduler or TaskScheduler.current(),
                interrupt = self.__interrupt,
            ).run(
                process,
                queue_in,
                queue_out
            )
            for _ in range(parallelism)
        ]

        def success(task: Task[Any], tasks: Sequence[Task[Any]]):
            if not output_queue:
                queue_out.complete()

        def cancel(task: Task[Any], tasks: Sequence[Task[Any]]):
            exceptions: dict[int, Exception] = {}
            for canceled_task in [ task for task in tasks if task.is_canceled ]:
                exception = canceled_task.exception
                if isinstance(exception, InterruptException):
                    exceptions[exception.interrupt.signal_id or 0] = exception
                else:
                    pass

            if len(exceptions) == 1:
                queue_out.fail(tuple(exceptions.values())[0])
            else:
                queue_out.fail(AggregateException(tuple(exceptions.values()))) # pragma: no cover -- should never happen sinde underlying tasks will always have the same interrupt

        def fail(task: Task[Any], tasks: Sequence[Task[Any]]):
            exception = AggregateException(tuple(cast(Exception, task.exception) for task in tasks if task.is_failed ))
            queue_out.fail(exception)


        task_success = Task.with_all(tasks, options=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE).run(success)
        task_canceled = Task.with_any(tasks, options=ContinuationOptions.ON_CANCELED | ContinuationOptions.INLINE).run(cancel)
        task_failed = Task.with_any(tasks, options=ContinuationOptions.ON_FAILED | ContinuationOptions.INLINE).run(fail)

        if not output_queue:
            return queue_out.get_iterator()
        else:
            return Task.with_any([task_success, task_canceled, task_failed]).plan()

def process(
    items: Iterable[Tin], /,
    task_name: str | None = None,
    parallelism: int | None = None,
    interrupt: Interrupt | None = None,
    scheduler: TaskScheduler | None = None,
) -> ProcessProto[Tin]:

    return ProcessProto(
        items,
        task_name,
        parallelism,
        interrupt,
        scheduler
    )
