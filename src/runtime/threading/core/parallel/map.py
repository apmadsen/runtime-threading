from typing import Iterable, Callable, TypeVar, Generic, ParamSpec, Concatenate

from runtime.threading.core.tasks.interrupt_signal import InterruptSignal
from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.parallel.process import process
from runtime.threading.core.tasks.helpers import get_function_name
from runtime.threading.core.parallel.parallel_context import ParallelContext
from runtime.threading.core.parallel.p_iterable import PIterable

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")
P = ParamSpec("P")

class MapProto(Generic[Tin]):
    __slots__ = [ "__items", "__name", "__parallelism", "__interrupt", "__scheduler" ]

    def __init__(
        self,
        items: Iterable[Tin],
        name: str | None = None,
        parallelism: int | None = None,
        interrupt: Interrupt = Interrupt.none(),
        scheduler: TaskScheduler | None = None
    ):
        self.__name = name
        self.__items = items
        self.__parallelism = parallelism
        self.__interrupt = interrupt
        self.__scheduler = scheduler

    def do(
        self,
        fn: Callable[Concatenate[Task[Tin], Tin, P], Iterable[Tout]], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> PIterable[Tout]:

        pc = ParallelContext.current()
        scheduler = self.__scheduler or TaskScheduler.current() if pc == ParallelContext.root() else pc.scheduler
        signal = InterruptSignal(self.__interrupt, pc.interrupt)
        interrupt = signal.interrupt
        parallelism = max(self.__parallelism or 0, pc.max_parallelism)

        output = process(
            self.__items,
            task_name = self.__name or get_function_name(fn) or None,
            parallelism = parallelism,
            interrupt = interrupt,
            scheduler = scheduler
        ).do(
            fn,
            *args,
            **kwargs
        )

        return output


def map(
    items: Iterable[Tin], /,
    task_name: str | None = None,
    parallelism: int | None = None,
    interrupt: Interrupt = Interrupt.none(),
    scheduler: TaskScheduler | None = None,
) -> MapProto[Tin]:

    return MapProto(
        items,
        task_name,
        parallelism,
        interrupt,
        scheduler
    )
