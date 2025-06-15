from __future__ import annotations
from threading import RLock, Lock as TLock
from typing import overload, TYPE_CHECKING
from types import TracebackType
from datetime import datetime

from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER, POLL_INTERVAL

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.interrupt import Interrupt

class Lock:
    __slots__ = ["__lock"]

    def __init__(self, reentrant: bool = True):
        """Creates a new lock.

        Args:
            reentrant (bool, optional): Allow same task to acquire lock multiple times. Defaults to True.
        """

        self.__lock = RLock() if reentrant else TLock()

    @overload
    def acquire(self) -> bool:
        """Acquires the lock.

        Returns:
            bool: A boolean value indicating if lock was acquired or not.
        """
        ...
    @overload
    def acquire(self, *, interrupt: Interrupt) -> bool:
        """Acquires the lock.

        Args:
            interrupt (Interrupt): The Interrupt. Defaults to None.

        Returns:
            bool: A boolean value indicating if lock was acquired or not.
        """
        ...
    @overload
    def acquire(self, timeout: float | None) -> bool:
        """Acquires the lock.

        Args:
            timeout (float): The timeout. A value of 0 returns immediately without blocking

        Returns:
            bool: A boolean value indicating if lock was acquired or not.
        """
        ...
    @overload
    def acquire(self, timeout: float | None, *, interrupt: Interrupt) -> bool:
        """Acquires the lock.

        Args:
            timeout (float): The timeout. A value of 0 returns immediately without blocking
            interrupt (Interrupt): The Interrupt. Defaults to None.

        Returns:
            bool: A boolean value indicating if lock was acquired or not.
        """
        ...
    def acquire(self, timeout: float | None = None, *, interrupt: Interrupt | None = None) -> bool:
        start_time = datetime.now()
        if timeout and timeout < 0: # pragma: no cover
            raise ValueError("'timeout' must be a non-negative number")

        if interrupt:
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
            if interrupt:
                result = False
                while not interrupt.is_signaled:
                    result = self.__lock.acquire(True, min(POLL_INTERVAL, timeout or POLL_INTERVAL))
                    if result:
                        return result
                    elif timeout and (datetime.now()-start_time).total_seconds() >= timeout:
                        return False
                interrupt.raise_if_signaled()
                return result
            else:
                return self.__lock.acquire(True, timeout or -1)


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
        self.__lock.release()