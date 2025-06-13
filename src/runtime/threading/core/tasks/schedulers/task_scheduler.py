from __future__ import annotations
from threading import Thread, RLock, current_thread, main_thread
from typing import ContextManager, Any, TYPE_CHECKING
from abc import ABC, abstractmethod
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from runtime.threading.core.tasks.task import Task

LOCK = RLock()
THREADS: WeakKeyDictionary[Thread, tuple[TaskScheduler, Task[Any] | None]] = WeakKeyDictionary()

class TaskScheduler(ABC):
    __slots__ = ["__lock"]
    __default__: TaskScheduler

    def __init__(self):
        self.__lock = RLock()


    @property
    def synchronization_lock(self) -> RLock:
        """The internal synchronization lock
        """
        return self.__lock

    @classmethod
    def default(cls) -> TaskScheduler:
        """Returns the default task scheduler
        """
        with LOCK:
            if not hasattr(TaskScheduler, "__default__"):
                from runtime.threading.core.tasks.schedulers.concurrent_task_scheduler import ConcurrentTaskScheduler
                setattr(TaskScheduler, "__default__", ConcurrentTaskScheduler())
            return TaskScheduler.__default__

    @classmethod
    def current(cls) -> TaskScheduler:
        """Returns the task scheduler of the currently running task, or the default task scheduler if not called from within a running task

        Returns:
            TaskScheduler: The task scheduler of the currently running task, or the default task scheduler
        """
        cur_thread = current_thread()
        with LOCK:
            if cur_thread in THREADS:
                return THREADS[cur_thread][0]
            else:
                return TaskScheduler.default()

    @classmethod
    def current_task(cls) -> Task[Any] | None:
        """Returns the currently running task, if any

        Returns:
            Task | None: The currently running task
        """
        cur_thread = current_thread()
        with LOCK:
            if cur_thread in THREADS:
                return THREADS[cur_thread][1]
            else:
                return None

    def _register(self) -> None:
        """Registers the current thread on the task scheduler
        """
        cur_thread = current_thread()
        with LOCK:
            THREADS[cur_thread] = (self, None)

    def _run(self, task: Task[Any]) -> None:
        """Runs the specified task on the current thread

        Arguments:
            task (Task): The task to run
        """
        cur_thread = current_thread()

        with LOCK:
            THREADS[cur_thread] = (self, task)

        if cur_thread != main_thread():
            cur_thread.name = task.name

        task.run_synchronously()

    def _resume(self, task: Task[Any]) -> None:
        """Resumes the specified task on the current thread

        Arguments:
            task (Task): The task to run
        """
        cur_thread = current_thread()

        with LOCK:
            THREADS[cur_thread] = (self, task)

        if cur_thread != main_thread():
            cur_thread.name = task.name

    def _refresh_task(self) -> None:
        """Refreshes task info, like the name.
        """

        cur_thread = current_thread()
        cur_task = TaskScheduler.current_task()
        if cur_task:
            with LOCK:
                if current_thread() != main_thread():
                    cur_thread.name = cur_task.name

    def _unregister(self) -> None:
        """Un-registers the current thread on the task scheduler
        """
        cur_thread = current_thread()
        with LOCK:
            del THREADS[cur_thread]

    @abstractmethod
    def queue(self, task: Task[Any]) -> None:
        """Queues the task.

        Arguments:
            task (Task): The task to schedule
        """
        ...

    @abstractmethod
    def prioritise(self, task: Task[Any]) -> None:
        """Runs the task inline of another.

        Arguments:
            task (Task): The task to run
        """
        ...

    @abstractmethod
    def suspend(self) -> ContextManager[Any]:
        """Suspends the current task, ie. when waiting on an event.
        """
        ...

