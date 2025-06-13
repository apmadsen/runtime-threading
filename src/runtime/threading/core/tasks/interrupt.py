from __future__ import annotations
from typing import Callable
from weakref import WeakKeyDictionary, WeakSet

from runtime.threading.core.tasks.event import Event
from runtime.threading.core.tasks.lock import Lock

LOCK = Lock()
LINKED_INTERRUPTS: WeakKeyDictionary[Interrupt, WeakSet[Interrupt]] = WeakKeyDictionary()


class Interrupt:
    """The Interrupt class is used for asynchronous task cancellation. The Interrupt instance can be passed around between tasksc
    and used to poll for cancellation, while the InterruptSignal is used for signaling the Interrupt."""

    __slots__ = ["__lock", "__is_signaled", "__event", "__ex", "__weakref__"]
    __none__: Interrupt

    def __init__(self):
        self.__lock = Lock()
        self.__is_signaled = False
        self.__event = Event()
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

    @classmethod
    def none(cls) -> Interrupt:
        """Returns an empty Interrupt which cannot be signaled
        """
        if not hasattr(Interrupt, "__none__"):
            Interrupt.__none__ = Interrupt()
        return Interrupt.__none__


    @classmethod
    def _create(cls, *linked_interrupts: Interrupt) -> tuple[Interrupt, Callable[[], None]]:
        new_token = Interrupt()
        if linked_interrupts:
            with LOCK:
                for interrupt in linked_interrupts:
                    if interrupt is not Interrupt.none():
                        if interrupt not in LINKED_INTERRUPTS:
                            LINKED_INTERRUPTS[interrupt] = WeakSet([new_token])
                        else:
                            LINKED_INTERRUPTS[interrupt].add(new_token)

        return (new_token, new_token.__set)

    def __set(self) -> None:
        with self.__lock:
            from runtime.threading.core.tasks.task_interrupt_exception import TaskInterruptException
            self.__ex = TaskInterruptException(self)
            self.__is_signaled = True
            self.__event.set()

            with LOCK:
                if self in LINKED_INTERRUPTS:
                    for interrupt in LINKED_INTERRUPTS[self]:
                        if not interrupt.is_signaled:
                            interrupt.__set()

                    del LINKED_INTERRUPTS[self]

    def raise_if_signaled(self) -> None:
        """Raises a TaskCanceledException if signaled to cancel.
        """
        with self.__lock:
            if self.__is_signaled and self.__ex:
                raise self.__ex