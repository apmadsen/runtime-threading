from __future__ import annotations
from typing import Sequence, Any, TYPE_CHECKING

from runtime.threading.core.continuation import ContinueWhen, Continuation
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.task_state import TaskState
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.interrupt_exception import InterruptException

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.tasks.task import Task
    from runtime.threading.core.interrupt import Interrupt

class TasksContinuation(Continuation):
    __slots__ = [ "__what", "__then", "__options", "__states", "__done" ]

    def __init__(
        self, when: ContinueWhen,
        tasks: Sequence[Task[Any]],
        then: Task[Any],
        options: ContinuationOptions,
        interrupt: Interrupt | None
    ):
        super().__init__(when, [ t.wait_event for t in tasks ], interrupt)
        self.__what = tasks
        self.__then = then
        self.__options = options
        self.__states: set[TaskState] = set()
        self.__done = False

        if (options & ContinuationOptions.ON_INTERRUPTED) == ContinuationOptions.ON_INTERRUPTED:
            self.__states |= set([TaskState.INTERRUPTED])
        if (options & ContinuationOptions.ON_FAILED) == ContinuationOptions.ON_FAILED:
            self.__states |= set([TaskState.FAILED])
        if (options & ContinuationOptions.ON_COMPLETED_SUCCESSFULLY) == ContinuationOptions.ON_COMPLETED_SUCCESSFULLY:
            self.__states |= set([TaskState.COMPLETED])


    def try_continue(self) -> bool:
        with super().synchronization_lock:
            from runtime.threading.core.tasks.task import CompletedTask

            try:
                if self.__done:
                    return True
                elif not Continuation.try_continue(self):
                    return False
                else:
                    missing = [ task for task in self.__what if not task.is_completed ]
                    states = set([ task.state for task in self.__what ])
                    result: bool | None = None

                    if self.when == ContinueWhen.ALL:
                        if states.issubset(self.__states):
                            pass
                        elif not any(missing): # on or more tasks are in a wrong state
                            self.__then._interrupt_and_notify() # pyright: ignore[reportPrivateUsage]
                            result = True
                        else:
                            pass
                    elif self.when == ContinueWhen.ANY:
                        if (self.__options & ContinuationOptions.ON_COMPLETED_SUCCESSFULLY == ContinuationOptions.ON_COMPLETED_SUCCESSFULLY) and TaskState.COMPLETED in states:
                            pass
                        elif (self.__options & ContinuationOptions.ON_FAILED == ContinuationOptions.ON_FAILED) and TaskState.FAILED in states:
                            pass
                        elif (self.__options & ContinuationOptions.ON_INTERRUPTED == ContinuationOptions.ON_INTERRUPTED) and TaskState.INTERRUPTED in states:
                            pass
                        elif not any(missing):
                            self.__then._interrupt_and_notify() # pyright: ignore[reportPrivateUsage]
                            result = True
                        else:
                            result = False
                    else:
                        pass

                    if result is None:
                        if self.__options & ContinuationOptions.INLINE == ContinuationOptions.INLINE or isinstance(self.__then, CompletedTask):
                            TaskScheduler.current()._run(self.__then) # pyright: ignore[reportPrivateUsage]
                        else:
                            TaskScheduler.current().queue(self.__then)

                        result = True

                    if result is True:
                        self.__done = True
                        self.__what = ()
                        del self.__then

                    return result

            except InterruptException:
                self.__then._interrupt_and_notify() # pyright: ignore[reportPrivateUsage]
                self.__done = True
                self.__what = ()
                del self.__then
                raise
