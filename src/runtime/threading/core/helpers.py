from typing import Callable, ContextManager
from types import TracebackType
from threading import Thread

from runtime.threading.core.event import terminate_event
from runtime.threading.core.lock import Lock
from runtime.threading.core.semaphore import Semaphore
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.interrupt_signal import InterruptSignal

def signal_after(signal: InterruptSignal, time: float) -> None:
    """Creates a task which signals an InterruptSignal instance after a certain
    amount of time (seconds).

    Args:
        signal (InterruptSignal): The InterruptSignal instance to signal.
        time (float): The amount of time (seconds) before signaling.
    """
    def fn_signal():
        terminate_event.wait(time)
        signal.signal()

    t = Thread(target = fn_signal)
    t.start()
    t.join()


def acquire_or_fail(
    lock: Lock | Semaphore,
    timeout: float,
    fail: Callable[[], Exception],
    interrupt: Interrupt | None = None
) -> ContextManager[None]:
    """Tries to acquire lock for a specific period of time, and, if unsuccessful,
    raises a specific exception after timeout.

    Args:
        lock (Lock|Semaphore): The lock or semaphore.
        timeout (float): The timeout in seconds after which exception is thrown.
        fail (Callable[[], Exception]): The exception generator function.
        interrupt (Interrupt, optional): The Interrupt. Defaults to None.
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

