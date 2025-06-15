from typing import Callable, ContextManager
from types import TracebackType

from runtime.threading.core.lock import Lock
from runtime.threading.core.semaphore import Semaphore
from runtime.threading.core.interrupt import Interrupt




def acquire_or_fail(lock: Lock | Semaphore, timeout: float, fail: Callable[[], Exception], interrupt: Interrupt = Interrupt.none()) -> ContextManager[None]:
    """Tries to acquire lock for a specific period of time, and raises a specific exception after timeout.

    Args:
        lock (Lock | Semaphore): The lock opr semaphore.
        timeout (float): The timeout in seconds after which an exception is thrown.
        fail (Callable[[], Exception]): The exception generator function.
        interrupt (Interrupt, optional): The Interrupt. Defaults to Interrupt.none().
    """

    if lock.acquire(timeout, interrupt = interrupt):
        class Ctx:
            __slots__ = [ "__lock" ]

            def __init__(self, lock: Lock | Semaphore):
                self.__lock = lock

            def __enter__(self) -> None:
                pass
            def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None):
                self.__lock.release()

        return Ctx(lock)
    else:
        raise fail()

