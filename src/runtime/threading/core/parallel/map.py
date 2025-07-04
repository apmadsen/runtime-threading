from typing import Iterable, Callable, TypeVar, Generic, ParamSpec, Concatenate

from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.defaults import DEFAULT_PARALLELISM
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.parallel.process import process
from runtime.threading.core.tasks.helpers import get_function_name
from runtime.threading.core.parallel.pipeline.p_iterable import PIterable

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")
P = ParamSpec("P")

class MapProto(Generic[Tin]):
    """The MapProto class is an intermediary wrapper used to create a parallel mapping process.
    """
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

    def do(
        self,
        fn: Callable[Concatenate[Task[Iterable[Tout]], Tin, P], Iterable[Tout]], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> PIterable[Tout]:
        """Initiates parallel mapping process immediately.

        Args:
            fn (Callable[Concatenate[Task[Tin], Tin, P], Iterable[Tout]]): The target function

        Returns:
            PIterable[Tout]: Returns an iterator.
        """

        parallelism = max(1, self.__parallelism or DEFAULT_PARALLELISM)

        output = process(
            self.__items,
            task_name = self.__task_name or get_function_name(fn) or None,
            parallelism = parallelism,
            scheduler = self.__scheduler or TaskScheduler.current(),
            interrupt = self.__interrupt
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
    interrupt: Interrupt | None = None,
    scheduler: TaskScheduler | None = None
) -> MapProto[Tin]:
    """Initiates a parallel mapping process.

    Args:
        items (Iterable[Tin]): The items to process.
        task_name (str | None, optional): A custon task name. Defaults to None.
        parallelism (int | None, optional): The no. of tasks to run. Defaults to None.
        interrupt (Interrupt | None, optional): An external Interrupt for the operation. Defaults to None.
        scheduler (TaskScheduler | None, optional): The scheduler upon which the tasks will be scheduled. Defaults to None.

    Returns:
        MapProto[Tin]: Returns a ProcessProto wrapper.
    """

    return MapProto(
        items,
        task_name,
        parallelism,
        interrupt,
        scheduler
    )
