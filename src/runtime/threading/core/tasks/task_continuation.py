# from __future__ import annotations
# from typing import Any, TYPE_CHECKING

# from runtime.threading.core.continuation import ContinueWhen, Continuation
# from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
# from runtime.threading.core.tasks.task_state import TaskState
# from runtime.threading.core.tasks.continuation_options import ContinuationOptions
# from runtime.threading.core.interrupt_exception import InterruptException

# if TYPE_CHECKING: # pragma: no cover
#     from runtime.threading.core.tasks.task import Task
#     from runtime.threading.core.interrupt import Interrupt

# class TaskContinuation(Continuation):
#     __slots__ = [ "__what", "__then", "__options", "__done" ]

#     def __init__(
#         self,
#         task: Task[Any],
#         then: Task[Any],
#         options: ContinuationOptions,
#         interrupt: Interrupt | None
#     ):
#         super().__init__(ContinueWhen.ALL, [task.wait_event], interrupt)
#         self.__what = task
#         self.__then = then
#         self.__options = options
#         self.__done = False

#     def try_continue(self) -> bool:
#         with super().synchronization_lock:
#             from runtime.threading.core.tasks.task import CompletedTask

#             try:
#                 if self.__done:
#                     return True # pragma no cover
#                 elif not super().try_continue():
#                     return False # pragma no cover
#                 else:
#                     result: bool | None = None

#                     if self.__what.state == TaskState.COMPLETED and (self.__options & ContinuationOptions.ON_COMPLETED_SUCCESSFULLY == ContinuationOptions.ON_COMPLETED_SUCCESSFULLY):
#                         pass
#                     elif self.__what.state == TaskState.FAILED and (self.__options & ContinuationOptions.ON_FAILED == ContinuationOptions.ON_FAILED):
#                         pass
#                     elif self.__what.state == TaskState.CANCELED and (self.__options & ContinuationOptions.ON_CANCELED == ContinuationOptions.ON_CANCELED):
#                         pass
#                     else:
#                         self.__then._cancel_and_notify() # pyright: ignore[reportPrivateUsage]
#                         result = True

#                     if result is None:
#                         if self.__options & ContinuationOptions.INLINE == ContinuationOptions.INLINE or isinstance(self.__then, CompletedTask):
#                             TaskScheduler.current()._run(self.__then) # pyright: ignore[reportPrivateUsage]
#                         else:
#                             TaskScheduler.current().queue(self.__then)

#                         result = True
#                     else:
#                         pass # pragma no cover

#                     if result is True:
#                         self.__done = True
#                         del self.__what
#                         del self.__then
#                     else:
#                         pass # pragma no cover

#                     return result

#             except InterruptException:
#                 self.__then._cancel_and_notify() # pyright: ignore[reportPrivateUsage]
#                 self.__done = True
#                 del self.__what
#                 del self.__then
#                 raise