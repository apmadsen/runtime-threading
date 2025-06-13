from __future__ import annotations
from typing import Sequence, Iterable, TYPE_CHECKING

from runtime.threading.core.tasks.continue_when import ContinueWhen

if TYPE_CHECKING:
    from runtime.threading.core.tasks.event import Event

class Continuation:
    __slots__ = ["__when", "__what", "__done"]

    def __init__(self, when: ContinueWhen, events: Sequence[Event]):
        self.__when = when
        self.__what = tuple(events)
        self.__done = False

    @property
    def when(self) -> ContinueWhen:
        return self.__when

    @property
    def events(self) -> Iterable[Event]:
        return self.__what

    def try_continue(self) -> bool:
        if self.__done:
            return True

        missing = len(tuple( t for t in self.__what if not t.is_set ))

        if (
            self.__when == ContinueWhen.ALL and missing == 0 or
            self.__when == ContinueWhen.ANY and missing < len(self.__what)
        ):
            self.__done = True
            return True
        else:
            return False
