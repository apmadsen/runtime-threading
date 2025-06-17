from threading import RLock, Lock as TLock

from runtime.threading.core.lock_base import LockBase

class Lock(LockBase):
    __slots__ = [ ]

    def __init__(self, reentrant: bool = True):
        """Creates a new lock.

        Args:
            reentrant (bool, optional): Allow same task to acquire lock multiple times. Defaults to True.
        """

        super().__init__(RLock() if reentrant else TLock())
