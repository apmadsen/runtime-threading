from threading import RLock, Lock as TLock

from runtime.threading.core.lock_base import LockBase

class Lock(LockBase):
    """The Lock class limits concurrent access to objects by only allowing one single thread to
    acquire and hold it at any given time."""
    __slots__ = [ ]

    def __init__(self, reentrant: bool = True):
        """Creates a new lock.

        Args:
            reentrant (bool, optional): Allow same thread to acquire lock multiple times recursively. Defaults to True.
        """

        super().__init__(RLock() if reentrant else TLock())
