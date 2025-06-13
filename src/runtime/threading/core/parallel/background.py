from typing import Callable, Concatenate, ParamSpec, TypeVar

from runtime.threading.core.tasks.interrupt_signal import InterruptSignal
from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.parallel.parallel_context import ParallelContext
from runtime.threading.core.tasks.helpers import get_function_name

P = ParamSpec("P")
T = TypeVar("T")


class BackgroundProto:
    __slots__ = [ "__task_name", "__parallelism", "__interrupt", "__scheduler" ]

    def __init__(
        self,
        task_name: str | None = None,
        parallelism: int | None = None,
        interrupt: Interrupt = Interrupt.none(),
        scheduler: TaskScheduler | None = None
    ):
        self.__task_name = task_name
        self.__parallelism = parallelism
        self.__interrupt = interrupt
        self.__scheduler = scheduler

    def do(
        self,
        fn: Callable[Concatenate[Task[None], P], None], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[None]:

        pc = ParallelContext.current()
        scheduler = self.__scheduler or TaskScheduler.current() if pc == ParallelContext.root() else pc.scheduler
        signal = InterruptSignal(self.__interrupt, pc.interrupt)
        interrupt = signal.interrupt
        parallelism = max(self.__parallelism or 0, pc.max_parallelism)

        return Task.with_all([
            Task.create(
                name = self.__task_name or get_function_name(fn) or None,
                scheduler = scheduler,
                interrupt = interrupt,
            ).run(
                fn,
                *args,
                **kwargs
            )
            for _ in range(parallelism)
        ]).task()

def background(
    *,
    task_name: str | None = None,
    parallelism: int | None = None,
    interrupt: Interrupt = Interrupt.none(),
    scheduler: TaskScheduler | None = None
) -> BackgroundProto:

    return BackgroundProto(task_name, parallelism, interrupt, scheduler)