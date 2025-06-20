from __future__ import annotations
from typing import Callable, Concatenate, ParamSpec, TypeVar, ClassVar

from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.helpers import get_function_name

P = ParamSpec("P")
T = TypeVar("T")


class BackgroundProto:
    __slots__ = [ "__task_name", "__parallelism", "__interrupt", "__scheduler" ]
    __default__: ClassVar[BackgroundProto | None] = None

    def __new__(
        cls,
        task_name: str | None = None,
        parallelism: int | None = None,
        interrupt: Interrupt | None = None,
        scheduler: TaskScheduler | None = None
    ):
        if task_name is parallelism is interrupt is scheduler is None:
            if BackgroundProto.__default__ is None:
                BackgroundProto.__default__ = super().__new__(cls)
            return BackgroundProto.__default__
        else:
            return super().__new__(cls)

    def __init__(
        self,
        task_name: str | None = None,
        parallelism: int | None = None,
        interrupt: Interrupt | None = None,
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

        parallelism = max(1, self.__parallelism or 2)

        return Task.with_all([
            Task.create(
                name = self.__task_name or get_function_name(fn) or None,
                scheduler = self.__scheduler or TaskScheduler.current(),
                interrupt = self.__interrupt,
            ).run(
                fn,
                *args,
                **kwargs
            )
            for _ in range(parallelism)
        ]).plan()

def background(
    *,
    task_name: str | None = None,
    parallelism: int | None = None,
    interrupt: Interrupt | None = None,
    scheduler: TaskScheduler | None = None
) -> BackgroundProto:

    return BackgroundProto(task_name, parallelism, interrupt, scheduler)