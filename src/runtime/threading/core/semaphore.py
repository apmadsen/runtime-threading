from threading import BoundedSemaphore

from runtime.threading.core.lock_base import LockBase

class Semaphore(LockBase):
    """The Semaphore class acts as a lock which allows a preset no. of simultaneous connections before blocking,
    as opposed to a stabdard lock which allows only one connection at a time."""

    __slots__ = [ ]

    def __init__(self, max_connections: int = 1):
        """Creates a new Semaphore.

        Args:
            max_connections (bool): The maximum no of simeltaneous connections to be allowed before blocking. Defaults to 1.
        """

        super().__init__(BoundedSemaphore(max_connections))
