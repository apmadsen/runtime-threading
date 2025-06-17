from __future__ import annotations
from typing import Any, TYPE_CHECKING

from runtime.threading.core.tasks.continuation import ContinueWhen, Continuation
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.task_state import TaskState
from runtime.threading.core.tasks.continuation_options import ContinuationOptions

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.tasks.task import Task

class TaskContinuation(Continuation):
    __slots__ = ["__what", "__then", "__options"]
    def __init__(self, task: Task[Any], then: Task[Any], options: ContinuationOptions):
        super().__init__(ContinueWhen.ALL, [task.wait_event])
        self.__what = task
        self.__then = then
        self.__options = options

    def try_continue(self) -> bool:
        from runtime.threading.core.tasks.task import CompletedTask

        if not super().try_continue():
            return False # pragma no cover
        else:
            if self.__what.state == TaskState.COMPLETED and (self.__options & ContinuationOptions.ON_COMPLETED_SUCCESSFULLY == ContinuationOptions.ON_COMPLETED_SUCCESSFULLY):
                pass
            elif self.__what.state == TaskState.FAILED and (self.__options & ContinuationOptions.ON_FAILED == ContinuationOptions.ON_FAILED):
                pass
            elif self.__what.state == TaskState.CANCELED and (self.__options & ContinuationOptions.ON_CANCELED == ContinuationOptions.ON_CANCELED):
                pass
            else:
                self.__then._cancel_and_notify() # pyright: ignore[reportPrivateUsage]
                return True

            if self.__options & ContinuationOptions.INLINE == ContinuationOptions.INLINE or isinstance(self.__then, CompletedTask):
                TaskScheduler.current()._run(self.__then) # pyright: ignore[reportPrivateUsage]
            else:
                TaskScheduler.current().queue(self.__then)

            return True
