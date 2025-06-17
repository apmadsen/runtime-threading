from threading import BoundedSemaphore

from runtime.threading.core.lock_base import LockBase

class Semaphore(LockBase):
    __slots__ = ["__semaphore"]

    def __init__(self, max_connections: int = 1):
        """Creates a new semaphore.

        Args:
            max_connections (bool): The maximum no of simeltaneous connections to be allowed before blocking. Defaults to 1.
        """

        super().__init__(BoundedSemaphore(max_connections))
