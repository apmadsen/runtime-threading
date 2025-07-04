from typing import Iterable, Callable, Concatenate, ParamSpec, TypeVar, Generic, Any
from collections.abc import Sized

from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.defaults import DEFAULT_PARALLELISM
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue
from runtime.threading.core.tasks.helpers import get_function_name

P = ParamSpec("P")
T = TypeVar("T")


class ForEachProto(Generic[T]):
    """The ForEachProto class is an intermediary wrapper used to create a parallel for-each process.
    """
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
        """Initiates parallel for-each process immediately.

        Args:
            fn (Callable[Concatenate[Task[None], T, P], None]): The target function

        Returns:
            Task[None]. Returns a task.
        """

        parallelism = max(1, self.__parallelism or DEFAULT_PARALLELISM)

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
    """Initiates a parallel for-each process.

    Args:
        items (Iterable[T]): The items to process.
        task_name (str | None, optional): A custon task name. Defaults to None.
        parallelism (int | None, optional): The no. of tasks to run. Defaults to None.
        interrupt (Interrupt | None, optional): An external Interrupt for the operation. Defaults to None.
        scheduler (TaskScheduler | None, optional): The scheduler upon which the tasks will be scheduled. Defaults to None.

    Returns:
        ForEachProto[Tin]: Returns a ProcessProto wrapper.
    """

    return ForEachProto(items, task_name, parallelism, interrupt, scheduler)