from __future__ import annotations
from typing import Callable, cast
from weakref import WeakSet
from collections import deque

from runtime.threading.core.event import Event
from runtime.threading.core.one_time_event import OneTimeEvent
from runtime.threading.core.lock import Lock

LOCK = Lock()

class Interrupt:
    """The Interrupt class is used for asynchronous task cancellation. The Interrupt instance can be passed around between tasksc
    and used to poll for cancellation, while the InterruptSignal is used for signaling the Interrupt."""

    __slots__ = ["__lock", "__signal", "__event", "__ex", "__linked", "__weakref__"]

    def __init__(self):
        self.__lock = Lock()
        self.__signal: int | None = None
        self.__event = OneTimeEvent()
        self.__linked: WeakSet[Interrupt] = WeakSet()
        self.__ex: Exception | None = None


    @property
    def is_signaled(self) -> bool:
        """Indicates if Interrupt has been signaled
        """
        with self.__lock:
            return self.__signal is not None

    @property
    def signal_id(self) -> int | None:
        with self.__lock:
            return self.__signal

    @property
    def wait_event(self) -> Event:
        """The internal event, handling signaling
        """
        return self.__event


    def propagates_to(self, interrupt: Interrupt) -> bool:
        """Indicates if this Interrupt instance is linked to other Interrupt. If true,
        signaling this Interrupt will propagate signal onto the other.
        Note: This information is not available after Interrupt has been signaled...
        """
        return self.__propagates_to(interrupt, deque())

    def __propagates_to(self, interrupt: Interrupt, stack: deque[Interrupt]) -> bool:
        stack.append(self)

        if interrupt in self.__linked:
            return True
        else:
            for linked in self.__linked:
                if linked not in stack and linked.__propagates_to(interrupt, stack.copy()):
                    return True

        return False

    @classmethod
    def _create(cls, *linked_interrupts: Interrupt) -> tuple[Interrupt, Callable[[int], None]]:
        new_token = Interrupt()
        if linked_interrupts:
            with LOCK:
                for interrupt in linked_interrupts:
                    if interrupt.is_signaled: # signal immediately and return
                        new_token.__set(cast(int, interrupt.signal_id))
                        break
                    else:
                        interrupt.__linked.add(new_token)

        return (new_token, new_token.__set)

    def __set(self, signal: int) -> None:
        with self.__lock:
            from runtime.threading.core.interrupt_exception import InterruptException
            self.__ex = InterruptException(self)
            self.__signal = signal
            self.__event.signal()

            for interrupt in self.__linked:
                if not interrupt.is_signaled:
                    interrupt.__set(signal)

            self.__linked.clear()

    def raise_if_signaled(self) -> None:
        """Raises an InterruptException if signaled.
        """
        with self.__lock:
            if self.signal_id is not None and self.__ex:
                raise self.__ex

    def wait(
        self,
        timeout: float | None = None, /,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Waits for a signal. Same as wait_handle.wait().
        """
        return self.__event.wait(timeout, interrupt)