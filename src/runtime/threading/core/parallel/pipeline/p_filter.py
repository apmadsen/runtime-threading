from typing import Callable, TypeVar, Iterable, overload

from runtime.threading.core.parallel.pipeline.p_fn import PFn
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.helpers import get_function_name

T = TypeVar("T")

class PFilter(PFn[T, T]):
    """The PFilter class is an extension of the base PFn class which applies a filter to the work items.
    The function is inclusive, meaning is uses a predefined predicate function to select the items
    it lets through.
    """
    __slots__ = ["__catch_all"]

    @overload
    def __init__(self) -> None:
        """Creates a new catch-all parallel filter function, i.e. one that doesn't filter out anything.
        """
        ...
    @overload
    def __init__(self, *, parallelism: int) -> None:
        """Creates a new catch-all parallel filter function, i.e. one that doesn't filter out anything.

        Args:
            parallelism (int): A no. between 1 and 32 representing the max no. of parallel threads.
        """
        ...
    @overload
    def __init__(self, fn: Callable[[Task[Iterable[T]], T], bool]) -> None:
        """Creates a new parallel filter function with a predicate function for selecting the
        work items it lets through.

        Args:
            fn (Callable[[Task[Iterable[T]], T], bool]): The predicate function used to to determine which items to let through.
        """
        ...
    @overload
    def __init__(self, fn: Callable[[Task[Iterable[T]], T], bool], *, parallelism: int) -> None:
        """Creates a new parallel filter function with a predicate function for selecting the
        work items it lets through.

        Args:
            fn (Callable[[Task[Iterable[T]], T], bool]): The The predicate function used to to determine which items to let through.
            parallelism (int): An int between 1 and 32 representing the max no. of parallel threads.
        """
        ...
    def __init__(self, fn: Callable[[Task[Iterable[T]], T], bool] | None = None, *, parallelism: int | float = 2):
        self.__catch_all = not fn
        def filter_fn(task: Task[Iterable[T]], item: T) -> Iterable[T]:
            if not fn:
                yield item # filter is a catch-all filter, i.e. it doesn't filter out anything
            else:
                org_task_name = task.name
                task.name = get_function_name(fn)
                if fn(task, item):
                    yield item
                task.name = org_task_name

        super().__init__(filter_fn, parallelism)


    @property
    def is_catch_all(self) -> bool:
        """Indicates if filter it a simple catch-all filter.
        """
        return self.__catch_all # pragma: no cover
