from __future__ import annotations
from threading import RLock, Lock as TLock, Semaphore
from typing import TYPE_CHECKING
from types import TracebackType
from datetime import datetime

from runtime.threading.core.defaults import TASK_SUSPEND_AFTER, POLL_INTERVAL
from runtime.threading.core.testing.debug import get_locks_debugger

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.interrupt import Interrupt

DEBUGGING = False

class LockBase:
    """The LockBase is the base class for locks and semaphores which share much of the the same logic.
    """
    __slots__ = [ "__internal_lock" ]

    def __init__(self, lock: RLock | TLock | Semaphore):
        self.__internal_lock = lock

    @property
    def _internal_lock(self) -> RLock | TLock | Semaphore:
        """The internal builtin lock or semaphore.
        """
        return self.__internal_lock

    def acquire(
        self,
        timeout: float | None = None,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Acquires the lock.

        Args:
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Raises:
            ValueError: A ValueError is raised if timeout is negative.

        Returns:
            bool: Returns True if lock was acquired, False otherwise.
        """
        try:
            if DEBUGGING and ( debugger := get_locks_debugger() ): # pragma: no cover
                debugger.register_lock_wait(self.__internal_lock)

            start_time = datetime.now()
            if timeout and timeout < 0: # pragma: no cover
                raise ValueError("'timeout' must be a non-negative number")

            if interrupt is not None:
                interrupt.raise_if_signaled()

            if timeout != None and timeout <= TASK_SUSPEND_AFTER:
                return self.__internal_lock.acquire(True, timeout)
            else:
                if self.__internal_lock.acquire(True, TASK_SUSPEND_AFTER):
                    return True
                elif timeout:
                    timeout -= TASK_SUSPEND_AFTER

            from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
            with TaskScheduler.current().suspend():
                if interrupt is not None:
                    while not interrupt.is_signaled:
                        if self.__internal_lock.acquire(True, min(POLL_INTERVAL, timeout or POLL_INTERVAL)):
                            return True
                        elif timeout and (datetime.now()-start_time).total_seconds() >= timeout:
                            return False

                    interrupt.raise_if_signaled() # pragma: no cover
                    return False # pragma: no cover
                else:
                    return self.__internal_lock.acquire(True, timeout or -1)

        finally:
            if DEBUGGING and ( debugger := get_locks_debugger() ): # pragma: no cover
                debugger.unregister_lock_wait(self.__internal_lock)

    def release(self):
        """Releases the lock.
        """
        self.__internal_lock.release()





    def __enter__(self) -> None:
        """Acquires the lock.
        """
        self.acquire()

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None):
        """Releases the lock.
        """
        self.release()