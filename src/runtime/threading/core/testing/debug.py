from __future__ import annotations
from typing import TYPE_CHECKING
from threading import Lock as TLock, RLock, Semaphore, Event as TEvent

from runtime.threading.core.testing.reflection import get_referrer

if TYPE_CHECKING:
    from runtime.threading.core.event import Event
    from runtime.threading.core.continuation import Continuation

DEBUGGING = False
EVENTS_DEBUGGER: EventsDebugger | None = None
LOCKS_DEBUGGER: LocksDebugger | None = None

def enable_debugging() -> tuple[EventsDebugger, LocksDebugger]: # pyright: ignore[reportReturnType] # pragma: no cover
    global DEBUGGING, EVENTS_DEBUGGER, LOCKS_DEBUGGER
    if not DEBUGGING:
        DEBUGGING = True # pyright: ignore[reportConstantRedefinition]
        EVENTS_DEBUGGER = EventsDebugger() # pyright: ignore[reportConstantRedefinition]
        LOCKS_DEBUGGER = LocksDebugger() # pyright: ignore[reportConstantRedefinition]

        import runtime.threading.core.event as events_module
        import runtime.threading.core.lock_base as locks_module
        events_module.DEBUGGING = True
        locks_module.DEBUGGING = True
        print("\n-- WARNING: EXTENSIVE DEBUGGING ENABLED --\n")
        return EVENTS_DEBUGGER, LOCKS_DEBUGGER

def get_events_debugger() -> EventsDebugger | None: # pragma: no cover
    return EVENTS_DEBUGGER

def get_locks_debugger() -> LocksDebugger | None: # pragma: no cover
    return LOCKS_DEBUGGER

class EventsDebugger: # pragma: no cover
    def __init__(self):
        from runtime.threading.core.lock import Lock
        self.__lock_waits = Lock()
        self.__lock_continuations = Lock()
        self.__continuations: dict[Event, set[Continuation]] = {}
        self.__waits: dict[TEvent, int] = {}

    def get_continuations(self) -> dict[Event, set[Continuation]]:
        with self.__lock_continuations:
            return self.__continuations.copy()

    def register_continuation(self, event: Event, continuation: Continuation):
        referrer = get_referrer(__file__)
        with self.__lock_continuations:
            setattr(continuation, "__referrer__", referrer)
            if not event in self.__continuations:
                self.__continuations[event] = set((continuation,))
            else:
                self.__continuations[event].add(continuation)

    def unregister_continuation(self, event: Event, continuation: Continuation | None = None):
        with self.__lock_continuations:
            if event in self.__continuations:
                if continuation is not None and continuation in self.__continuations[event]:
                    self.__continuations[event].remove(continuation)
                    if not self.__continuations[event]:
                        del self.__continuations[event]
                elif not self.__continuations[event]:
                    del self.__continuations[event]

    def get_waits(self) -> dict[TEvent, int]:
        with self.__lock_waits:
            return self.__waits.copy()

    def register_event_wait(self, event: TEvent):
        with self.__lock_waits:
            if not event in self.__waits:
                self.__waits[event] = 1
            else:
                self.__waits[event] += 1


    def unregister_event_wait(self, event: TEvent):
        with self.__lock_waits:
            if self.__waits[event] == 1:
                del self.__waits[event]
            else:
                self.__waits[event] -= 1


class LocksDebugger: # pragma: no cover
    def __init__(self):
        self.__lock_waits = RLock()
        self.__waits: dict[RLock | TLock | Semaphore, int] = {}

    def get_waits(self) -> dict[RLock | TLock | Semaphore, int]:
        with self.__lock_waits:
            return self.__waits.copy()

    def register_lock_wait(self, lock: RLock | TLock | Semaphore):
        with self.__lock_waits:
            if not lock in self.__waits:
                self.__waits[lock] = 1
            else:
                self.__waits[lock] += 1

    def unregister_lock_wait(self, lock: RLock | TLock | Semaphore):
        with self.__lock_waits:
            if self.__waits[lock] == 1:
                del self.__waits[lock]
            else:
                self.__waits[lock] -= 1

