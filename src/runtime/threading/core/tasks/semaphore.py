from __future__ import annotations
from threading import BoundedSemaphore
from typing import Any, overload, TYPE_CHECKING
from datetime import datetime

from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER, POLL_INTERVAL

if TYPE_CHECKING:
    from runtime.threading.core.tasks.interrupt import Interrupt

class Semaphore:
    __slots__ = ["__semaphore"]

    def __init__(self, max_connections: int = 1):
        """Creates a new semaphore.

        Args:
            max_connections (bool): The maximum no of simeltaneous connections to be allowed before blocking. Defaults to 1.
        """

        self.__semaphore = BoundedSemaphore(max_connections)

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
        if timeout and timeout < 0:
            raise ValueError("'timeout' must be a non-negative number")

        if interrupt:
            interrupt.raise_if_signaled()

        if timeout != None and timeout <= TASK_SUSPEND_AFTER:
            return self.__semaphore.acquire(True, timeout)
        else:
            if self.__semaphore.acquire(True, TASK_SUSPEND_AFTER):
                return True
            elif timeout:
                timeout -= TASK_SUSPEND_AFTER

        from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
        with TaskScheduler.current().suspend():
            if interrupt:
                result = False
                while not interrupt.is_signaled:
                    result = self.__semaphore.acquire(True, min(POLL_INTERVAL, timeout or POLL_INTERVAL))
                    if result:
                        return result
                    elif timeout and (datetime.now()-start_time).total_seconds() >= timeout:
                        return False
                interrupt.raise_if_signaled()
                return result
            else:
                return self.__semaphore.acquire(True, timeout)


    def release(self):
        """Releases the lock
        """
        self.__semaphore.release()


    def __enter__(self) -> None:
        """Acquires the lock.
        """
        self.acquire()

    def __exit__(self, *args: Any):
        """Releases the lock
        """
        self.__semaphore.release()