from typing import Callable, TypeVar, Iterable, overload

from runtime.threading.core.parallel.pipeline.p_fn import PFn
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.helpers import get_function_name
from runtime.threading.core.parallel.pipeline.pipeline_exception import PipelineException

T = TypeVar("T")

class PFilter(PFn[T, T]):
    """Filters the parallel data
    """
    __slots__ = ["__catch_all"]

    @overload
    def __init__(self) -> None:
        """Creates a new catch-all parallel filter function
        """
        ...
    @overload
    def __init__(self, *, parallelism: int) -> None:
        """Creates a new catch-all parallel filter function

        Args:
            parallelism (int): An int between 1 and 32 representing the max no. of parallel threads.
        """
        ...
    @overload
    def __init__(self, fn: Callable[[T], bool]) -> None:
        """Creates a new parallel filter function

        Args:
            fn (Callable[[Tin, Task[Tout]], Iterable[Tout]]): The function used to filter input data
        """
        ...
    @overload
    def __init__(self, fn: Callable[[T], bool], *, parallelism: int) -> None:
        """Creates a new parallel filter function

        Args:
            fn (Callable[[Tin, Task[Tout]], Iterable[Tout]]): The function used to filter input data
            parallelism (int): An int between 1 and 32 representing the max no. of parallel threads.
        """
        ...
    def __init__(self, fn: Callable[[T], bool] | None = None, *, parallelism: int | float = 2):
        self.__catch_all = not fn
        def filter_fn(task: Task[T], item: T) -> Iterable[T]:
            if not fn:
                yield item
            else:
                org_task_name = task.name
                task.name = get_function_name(fn)
                if fn(item):
                    yield item
                task.name = org_task_name

        super().__init__(filter_fn, parallelism)


    @property
    def is_catch_all(self) -> bool:
        return self.__catch_all # pragma: no cover
