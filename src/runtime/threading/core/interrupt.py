from __future__ import annotations
from typing import Callable, ClassVar, cast
from weakref import WeakSet
from collections import deque

from runtime.threading.core.event import Event
from runtime.threading.core.one_time_event import OneTimeEvent
from runtime.threading.core.lock import Lock

LOCK = Lock()

class Interrupt:
    """The Interrupt class is used for asynchronous task interruption. The Interrupt instance can be passed around between tasks
    and used to poll for interruption, while the InterruptSignal is used for signaling the Interrupt."""

    __slots__ = ["__lock", "__signal", "__notify_event", "__ex", "__linked", "__weakref__"]
    __none__: ClassVar[Interrupt | None] = None

    def __init__(self):
        self.__lock = Lock()
        self.__signal: int | None = None
        self.__notify_event = OneTimeEvent(purpose = "INTERRUPT_NOTIFY")
        self.__linked: WeakSet[Interrupt] = WeakSet()
        self.__ex: Exception | None = None


    @property
    def is_signaled(self) -> bool:
        """Indicates if Interrupt has been signaled.
        """
        with self.__lock:
            return self.__signal is not None

    @property
    def signal_id(self) -> int | None:
        """The id of the signal (if signaled).
        """
        with self.__lock:
            return self.__signal

    @property
    def wait_event(self) -> Event:
        """The internal event which handles signaling.
        """
        return self.__notify_event


    def propagates_to(self, interrupt: Interrupt) -> bool:
        """Indicates if this interrupt instance is linked to other interrupt. If true,
        signaling this interrupt will propagate signal onto the other.
        Note: This information is not available after interrupt has been signaled...
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

    @staticmethod
    def none() -> Interrupt:
        """Returns a default interrupt which will never be signaled.
        """
        with LOCK:
            if Interrupt.__none__ is None:
                Interrupt.__none__ = Interrupt()
            return Interrupt.__none__

    @staticmethod
    def _create(*linked_interrupts: Interrupt) -> tuple[Interrupt, Callable[[int], None]]:
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
            self.__notify_event.signal()

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
        """Waits for signal. Same as wait_handle.wait().

        Args:
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Returns:
            bool: Returns True if signaled, False otherwise.
        """
        return self.__notify_event.wait(timeout, interrupt)