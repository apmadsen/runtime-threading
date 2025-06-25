from __future__ import annotations
from typing import Sequence, TYPE_CHECKING

from runtime.threading.core.continue_when import ContinueWhen
from runtime.threading.core.lock import Lock

if TYPE_CHECKING: # pragma: no cover
    from runtime.threading.core.event import Event
    from runtime.threading.core.interrupt import Interrupt

class Continuation:
    __slots__ = [ "__lock", "__when", "__what", "__done", "__interrupt", "__referrer__" ]

    def __init__(
        self,
        when: ContinueWhen,
        events: Sequence[Event],
        interrupt: Interrupt | None
    ):
        self.__lock = Lock()
        self.__when = when
        self.__what = tuple(events)
        self.__done = False
        self.__interrupt = interrupt

        if interrupt and interrupt.wait_event not in events:
            self.__what = ( interrupt.wait_event, *events )

    @property
    def synchronization_lock(self) -> Lock:
        return self.__lock

    @property
    def when(self) -> ContinueWhen:
        return self.__when

    @property
    def events(self) -> Sequence[Event]:
        return self.__what

    @property
    def interrupt(self) -> Interrupt | None:
        return self.__interrupt

    @property
    def is_done(self) -> bool: # pragma: no cover
        return self.__done

    def try_continue(self) -> bool:
        with self.__lock:
            if self.__interrupt:
                interrupt_event = self.__interrupt.wait_event

                if self.__interrupt.is_signaled:
                    self.__interrupt.raise_if_signaled()
            else:
                interrupt_event = None

            if self.__done:
                return True

            missing = len(
                tuple(
                    event
                    for event in self.__what
                    if event is not interrupt_event and  not event.is_signaled
                )
            )

            if (
                self.__when == ContinueWhen.ALL and missing == 0 or
                self.__when == ContinueWhen.ANY and missing < len(self.__what)
            ):
                self.__done = True
                return True
            else:
                return False
