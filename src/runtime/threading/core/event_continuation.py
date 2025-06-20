from __future__ import annotations
from typing import Sequence, TYPE_CHECKING

from runtime.threading.core.continuation import Continuation
from runtime.threading.core.continue_when import ContinueWhen
from runtime.threading.core.interrupt_exception import InterruptException

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.event import Event
    from runtime.threading.core.interrupt import Interrupt

class EventContinuation(Continuation):
    __slots__ = [ "__event", "__done", "__weakref__" ]

    def __init__(
        self,
        when: ContinueWhen,
        events: Sequence[Event],
        then: Event,
        interrupt: Interrupt | None
    ):
        super().__init__(when, events, interrupt)
        self.__event = then
        self.__done = False

    def try_continue(self) -> bool:
        with super().synchronization_lock:
            try:
                if self.__done:
                    return True
                elif not super().try_continue():
                    return False
                else:
                    self.__event.signal()
                    self.__done = True
                    del self.__event
                    return True

            except InterruptException:
                self.__event.signal()
                self.__done = True
                del self.__event
                raise
