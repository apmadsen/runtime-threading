from typing import Callable, TypeVar, Iterable, ContextManager
from types import TracebackType
from runtime.threading.core.tasks.task import Task, get_function_name
from runtime.threading.core.tasks.lock import Lock
from runtime.threading.core.tasks.semaphore import Semaphore
from runtime.threading.core.tasks.interrupt import Interrupt

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")
Tnext = TypeVar("Tnext")


def envelop(fn: Callable[[Tout, Task[Tnext]], Iterable[Tnext]]) -> Callable[[Tout, Task[Tnext]], Iterable[Tnext]]:
    """Envelops a task function, to create a uniform type annotation.

    Args:
        fn (Callable[[Tout, Task[Tnext]], Iterable[Tnext]]): The function

    Returns:
        Callable[[Tout, Task[Tnext]], Iterable[Tnext]]: The enveloped function
    """
    return fn


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


__all__ = (
    'get_function_name',
    'envelop'
)