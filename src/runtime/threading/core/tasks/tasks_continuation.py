from __future__ import annotations
from typing import Sequence, Any, TYPE_CHECKING

from runtime.threading.core.tasks.continuation import ContinueWhen, Continuation
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.task_state import TaskState
from runtime.threading.core.tasks.continuation_options import ContinuationOptions

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.tasks.task import Task

class TasksContinuation(Continuation):
    __slots__ = ["__what", "__then", "__options", "__states"]
    def __init__(self, when: ContinueWhen, tasks: Sequence[Task[Any]], then: Task[Any], options: ContinuationOptions):
        super().__init__(when, [ t.wait_event for t in tasks ])
        self.__what = tasks
        self.__then = then
        self.__options = options
        self.__states: set[TaskState] = set()

        if (options & ContinuationOptions.ON_CANCELED) == ContinuationOptions.ON_CANCELED:
            self.__states |= set([TaskState.CANCELED])
        if (options & ContinuationOptions.ON_FAILED) == ContinuationOptions.ON_FAILED:
            self.__states |= set([TaskState.FAILED])
        if (options & ContinuationOptions.ON_COMPLETED_SUCCESSFULLY) == ContinuationOptions.ON_COMPLETED_SUCCESSFULLY:
            self.__states |= set([TaskState.COMPLETED])



    def try_continue(self) -> bool:
        from runtime.threading.core.tasks.task import CompletedTask

        if not Continuation.try_continue(self):
            return False
        else:
            missing = [ task for task in self.__what if not task.is_completed ]
            states = set([ task.state for task in self.__what ])

            if self.when == ContinueWhen.ALL:
                if states.issubset(self.__states):
                    pass
                elif not any(missing): # on or more tasks are in a wrong state
                    self.__then._cancel_and_notify() # pyright: ignore[reportPrivateUsage]
                    return True
                else:
                    pass # pragma: no cover
            elif self.when == ContinueWhen.ANY:
                if (self.__options & ContinuationOptions.ON_COMPLETED_SUCCESSFULLY == ContinuationOptions.ON_COMPLETED_SUCCESSFULLY) and TaskState.COMPLETED in states:
                    pass
                elif (self.__options & ContinuationOptions.ON_FAILED == ContinuationOptions.ON_FAILED) and TaskState.FAILED in states:
                    pass
                elif (self.__options & ContinuationOptions.ON_CANCELED == ContinuationOptions.ON_CANCELED) and TaskState.CANCELED in states:
                    pass
                elif not any(missing):
                    self.__then._cancel_and_notify() # pyright: ignore[reportPrivateUsage]
                    return True
                else:
                    return False
            else:
                pass # pragma: no cover

            if self.__options & ContinuationOptions.INLINE == ContinuationOptions.INLINE or isinstance(self.__then, CompletedTask):
                TaskScheduler.current()._run(self.__then) # pyright: ignore[reportPrivateUsage]
            else:
                TaskScheduler.current().queue(self.__then)

            return True
