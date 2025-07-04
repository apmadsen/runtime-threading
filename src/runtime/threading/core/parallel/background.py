from __future__ import annotations
from typing import Callable, Concatenate, ParamSpec, TypeVar, ClassVar

from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.defaults import DEFAULT_PARALLELISM
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.helpers import get_function_name

P = ParamSpec("P")
T = TypeVar("T")


class BackgroundProto:
    """The BackgroundProto class is an intermediary wrapper used to create a parallel background process.
    """
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
        """Initiates parallel processing immediately.

        Args:
            fn (Callable[Concatenate[Task[None], P], None]): The target function

        Returns:
            Task[None]. Returns a task.
        """

        parallelism = max(1, self.__parallelism or DEFAULT_PARALLELISM)

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
    """Initiates a parallel background process.

    Args:
        task_name (str | None, optional): A custon task name. Defaults to None.
        parallelism (int | None, optional): The no. of tasks to run. Defaults to None.
        interrupt (Interrupt | None, optional): An external Interrupt for the operation. Defaults to None.
        scheduler (TaskScheduler | None, optional): The scheduler upon which the tasks will be scheduled. Defaults to None.

    Returns:
        BackgroundProto: Returns a BackgroundProto wrapper.
    """

    return BackgroundProto(task_name, parallelism, interrupt, scheduler)