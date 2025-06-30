from __future__ import annotations
from threading import Thread, RLock, current_thread, main_thread
from typing import ContextManager, Any, ClassVar, TYPE_CHECKING
from abc import ABC, abstractmethod
from weakref import WeakKeyDictionary, finalize

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.tasks.task import Task

from runtime.threading.core.tasks.task_exception import TaskException

LOCK = RLock()
THREADS: WeakKeyDictionary[Thread, tuple[TaskScheduler, Task[Any] | None]] = WeakKeyDictionary()

SchedulerClosedError = TaskException("Task scheduler has been closed")
TaskAlreadyStartedOrScheduledError = TaskException("Task is already running or scheduled on another scheduler.")

class TaskScheduler(ABC):
    """The TaskScheduler class is the base task scheduler class responsible for managing the threads
    used by all derived schedulers.
    """

    __slots__ = [ "__lock", "__finalizer", "__finalizing", "__weakref__" ]
    __default__: ClassVar[TaskScheduler | None] = None

    def __init__(self):
        self.__lock = RLock()

        def fn_finalize(): # pragma: no cover
            self.__finalizing = True
            self.__finalize__()
            self.__finalizing = False

        self.__finalizing = False
        self.__finalizer = finalize(self, fn_finalize)

    @property
    def synchronization_lock(self) -> RLock:
        """The internal synchronization lock
        """
        return self.__lock

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        """Indicates if the scheduler has been closed.
        """
        ...

    @property
    def finalized(self) -> bool: # pragma: no cover
        """Indicates if object has been finalized or not.
        """
        return not self.__finalizer.alive

    @property
    def finalizing(self) -> bool: # pragma: no cover
        """Indicates if object is in the process of finalizing or not.
        """
        return self.__finalizing


    @staticmethod
    def default() -> TaskScheduler:
        """Returns the default task scheduler (a ConcurrentTaskScheduler instance).
        """
        with LOCK:
            if TaskScheduler.__default__ is None or TaskScheduler.__default__.is_closed or TaskScheduler.__default__.finalizing:
                from runtime.threading.core.tasks.schedulers.concurrent_task_scheduler import ConcurrentTaskScheduler
                TaskScheduler.__default__ = ConcurrentTaskScheduler()
            return TaskScheduler.__default__

    @staticmethod
    def current() -> TaskScheduler:
        """Returns the task scheduler of the currently running task, or the default task scheduler
        if not called from within a running task.
        """
        cur_thread = current_thread()
        with LOCK:
            if cur_thread in THREADS:
                return THREADS[cur_thread][0]
            else:
                return TaskScheduler.default()

    @staticmethod
    def current_task() -> Task[Any] | None:
        """Returns the currently running task, if called from within one.
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
        else:
            pass  # pragma: no cover

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
        else:
            pass

    def _refresh_task(self) -> None:
        """Refreshes task info, like the name.
        """
        if cur_task := TaskScheduler.current_task():
            with LOCK:
                cur_thread = current_thread()
                if cur_thread != main_thread():
                    cur_thread.name = cur_task.name
                else:
                    pass
        else:
            pass

    def _unregister(self) -> None:
        """Un-registers the current thread on the task scheduler
        """
        cur_thread = current_thread()
        with LOCK:
            del THREADS[cur_thread]

    @abstractmethod
    def queue(self, task: Task[Any]) -> None:
        """Queues the specified task.

        Arguments:
            task (Task): The task to schedule
        """
        ...

    @abstractmethod
    def prioritise(self, task: Task[Any]) -> None:
        """Runs the task inline of another. For internal use.

        Arguments:
            task (Task): The task to run
        """
        ...

    @abstractmethod
    def suspend(self) -> ContextManager[Any]:
        """Suspends the current task, ie. when waiting on an event.
        """
        ...

    @abstractmethod
    def __finalize__(self) -> None:
        """This function is invoked when finalization process is initiated."""
        ...
