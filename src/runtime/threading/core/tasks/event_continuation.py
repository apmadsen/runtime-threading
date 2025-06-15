from __future__ import annotations
from typing import Sequence, TYPE_CHECKING
from threading import Event as TEvent

from runtime.threading.core.tasks.continuation import Continuation
from runtime.threading.core.tasks.continue_when import ContinueWhen

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.event import Event

class EventContinuation(Continuation):
    __slots__ = ["__event"]
    def __init__(self, when: ContinueWhen, events: Sequence[Event], then: TEvent):
        super().__init__(when, events)
        self.__event = then

    def try_continue(self) -> bool:
        if not Continuation.try_continue(self):
            return False
        else:
            self.__event.set()
            return True
