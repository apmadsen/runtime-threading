from __future__ import annotations
from threading import RLock, Lock as TLock, Semaphore
from typing import TYPE_CHECKING
from types import TracebackType
from datetime import datetime

from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER, POLL_INTERVAL

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.interrupt import Interrupt

LOCK = RLock()
DEBUG = False
DEBUG_INT_WAITS: dict[RLock | TLock | Semaphore, int] = {}

class LockBase:
    __slots__ = ["__lock"]

    def __init__(self, lock: RLock | TLock | Semaphore):
        self.__lock = lock

    def acquire(
        self,
        timeout: float | None = None,
        interrupt: Interrupt | None = None
    ) -> bool:
        try:
            if DEBUG:
                with LOCK:
                    if not self.__lock in DEBUG_INT_WAITS:
                        DEBUG_INT_WAITS[self.__lock] = 1
                    else:
                        DEBUG_INT_WAITS[self.__lock] += 1

            start_time = datetime.now()
            if timeout and timeout < 0: # pragma: no cover
                raise ValueError("'timeout' must be a non-negative number")

            if interrupt is not None:
                interrupt.raise_if_signaled()

            if timeout != None and timeout <= TASK_SUSPEND_AFTER:
                return self.__lock.acquire(True, timeout)
            else:
                if self.__lock.acquire(True, TASK_SUSPEND_AFTER):
                    return True
                elif timeout:
                    timeout -= TASK_SUSPEND_AFTER

            from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
            with TaskScheduler.current().suspend():
                if interrupt is not None:
                    while not interrupt.is_signaled:
                        if self.__lock.acquire(True, min(POLL_INTERVAL, timeout or POLL_INTERVAL)):
                            return True
                        elif timeout and (datetime.now()-start_time).total_seconds() >= timeout:
                            return False

                    interrupt.raise_if_signaled() # pragma: no cover
                    return False # pragma: no cover
                else:
                    return self.__lock.acquire(True, timeout or -1)

        finally:
            if DEBUG:
                with LOCK:
                    if DEBUG_INT_WAITS[self.__lock] == 1:
                        del DEBUG_INT_WAITS[self.__lock]
                    else:
                        DEBUG_INT_WAITS[self.__lock] -= 1


    def release(self):
        """Releases the lock
        """
        self.__lock.release()


    def __enter__(self) -> None:
        """Acquires the lock.
        """
        self.acquire()

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None):
        """Releases the lock
        """
        self.release()