from typing import Iterable, Callable, Concatenate, ParamSpec, TypeVar, Generic, Any
from collections.abc import Sized

from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.parallel.pipeline.producer_consumer_queue import ProducerConsumerQueue
from runtime.threading.core.tasks.helpers import get_function_name

P = ParamSpec("P")
T = TypeVar("T")


class ForEachProto(Generic[T]):
    __slots__ = [ "__items", "__task_name", "__parallelism", "__interrupt", "__scheduler" ]

    def __init__(
        self,
        items: Iterable[T],
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
        fn: Callable[Concatenate[Task[None], T, P], None], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[None]:

        parallelism = max(1, self.__parallelism or 2)

        if isinstance(self.__items, Sized):
            count = len(self.__items)
            parallelism = min(parallelism, count)

        queue = ProducerConsumerQueue[T](self.__items)

        def process(task: Task[Any], queue: Iterable[T]):
            for item in queue:
                task.interrupt.raise_if_signaled()
                fn(task, item, *args, **kwargs)

        return Task.with_all([
            Task.create(
                name = self.__task_name or get_function_name(fn) or None,
                scheduler = self.__scheduler or TaskScheduler.current(),
                interrupt = self.__interrupt
            ).run(
                process,
                queue.get_iterator(),
                *args,
                **kwargs
            )
            for _ in range(parallelism)
        ]).plan()


def for_each(
    items: Iterable[T],
    task_name: str | None = None,
    parallelism: int | None = None,
    interrupt: Interrupt | None = None,
    scheduler: TaskScheduler | None = None
) -> ForEachProto[T]:
    """Performs work on each item in parallel.
    Note that PContext is used internally to get a scheduler instance and parallelism, if None, is set to the context's max_parallelism property.

    Args:
        items (Iterable[T]): The source items
        fn (Callable[T, Task]): The target function
        interrupt (Interrupt, optional): The Interrupt. Defaults to Defaults to None.

    Returns:
        Task: A continuation task
    """

    return ForEachProto(items, task_name, parallelism, interrupt, scheduler)