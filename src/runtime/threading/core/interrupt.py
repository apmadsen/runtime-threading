from __future__ import annotations
from typing import Callable
from weakref import WeakSet
from collections import deque

from runtime.threading.core.event import Event
from runtime.threading.core.lock import Lock

LOCK = Lock()

class Interrupt:
    """The Interrupt class is used for asynchronous task cancellation. The Interrupt instance can be passed around between tasksc
    and used to poll for cancellation, while the InterruptSignal is used for signaling the Interrupt."""

    __slots__ = ["__lock", "__is_signaled", "__event", "__ex", "__linked", "__weakref__"]
    __none__: Interrupt

    def __init__(self):
        self.__lock = Lock()
        self.__is_signaled = False
        self.__event = Event()
        self.__linked: WeakSet[Interrupt] = WeakSet()
        self.__ex: Exception | None = None


    @property
    def is_signaled(self) -> bool:
        """Indicates if Interrupt has been signaled
        """
        with self.__lock:
            return self.__is_signaled

    @property
    def wait_event(self) -> Event:
        """The internal event, handling signaling
        """
        return self.__event

    @property
    def is_none(self) -> bool:
        return self is Interrupt.__none__

    @classmethod
    def none(cls) -> Interrupt:
        """Returns an empty Interrupt which cannot be signaled
        """
        if not hasattr(Interrupt, "__none__"):
            Interrupt.__none__ = Interrupt()
        return Interrupt.__none__

    def propagates_to(self, interrupt: Interrupt) -> bool:
        """Indicates if this Interrupt instance is linked to other Interrupt. If true,
        signaling this Interrupt wil propagate signaling onto the other...
        """
        return self.__propagates_to(interrupt, deque())

    def __propagates_to(self, interrupt: Interrupt, stack: deque[Interrupt]) -> bool:
        stack.append(self)

        if self is interrupt:
            return True
        elif interrupt in self.__linked:
            return True
        else:
            for linked in self.__linked:
                if linked not in stack and linked.__propagates_to(interrupt, stack.copy()):
                    return True

        return False

    @classmethod
    def _create(cls, *linked_interrupts: Interrupt) -> tuple[Interrupt, Callable[[], None]]:
        new_token = Interrupt()
        if linked_interrupts:
            with LOCK:
                for interrupt in linked_interrupts:
                    if interrupt is not Interrupt.none():
                        new_token.__linked.add(interrupt)

                        interrupt.__linked.add(new_token)

        return (new_token, new_token.__set)

    def __set(self) -> None:
        with self.__lock:
            from runtime.threading.core.interrupt_exception import InterruptException
            self.__ex = InterruptException(self)
            self.__is_signaled = True
            self.__event.set()

            for interrupt in self.__linked:
                if not interrupt.is_signaled:
                    interrupt.__set()
            self.__linked.clear()

    def raise_if_signaled(self) -> None:
        """Raises a TaskCanceledException if signaled to cancel.
        """
        with self.__lock:
            if self.__is_signaled and self.__ex:
                raise self.__ex