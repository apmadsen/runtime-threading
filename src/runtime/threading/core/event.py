from __future__ import annotations
import sys
from threading import Event as TEvent, current_thread, main_thread
from typing import Sequence, Any, Literal, Annotated, overload, cast, TYPE_CHECKING
from signal import signal, SIGTERM, SIGINT
from time import time

from runtime.threading.core.lock import Lock
from runtime.threading.core.defaults import TASK_SUSPEND_AFTER, POLL_INTERVAL
from runtime.threading.core.continuation import Continuation
from runtime.threading.core.event_continuation import EventContinuation
from runtime.threading.core.continue_when import ContinueWhen
from runtime.threading.core.threading_exception import ThreadingException
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.testing.debug import get_events_debugger

if TYPE_CHECKING:
    from runtime.threading.core.interrupt import Interrupt

DEBUGGING = False

Purpose = Literal[ "USER", "TERMINATE", "CONTINUATION", "INTERRUPT_NOTIFY",
                   "CONCURRENT_TASK_SCHEDULER_CLOSE", "TASK_NOTIFY",
                   "CONCURRENT_QUEUE_NOTIFY", "PRODUCER_CONSUMER_QUEUE_NOTIFY" ]
class Event:
    """The Event class is used for synchronization between threads.
    """
    __slots__ = [ "__id", "__lock", "__purpose", "__internal_event", "__continuations", "__weakref__" ]

    @overload
    def __init__(self) -> None:
        """Creates a new Event.
        """
        ...
    @overload
    def __init__(self, *, purpose: Purpose = "USER") -> None:
        """Creates a new Event.

        Args:
            purpose (Purpose, optional): The event purpose (used for testing). Defaults to "USER".
        """
        ...
    @overload
    def __init__(self, internal_event: TEvent) -> None:
        """Creates an event from an existing builtin event.

        Args:
            internal_event (TEvent): The preexisting builtin event instance.
        """
        ...
    @overload
    def __init__(self, internal_event: TEvent, *, purpose: Purpose = "USER") -> None:
        """Creates an event from an existing builtin event.

        Args:
            internal_event (TEvent): The preexisting builtin event instance.
            purpose (Purpose, optional): The event purpose (used for testing). Defaults to "USER".
        """
        ...
    def __init__(self, internal_event: TEvent | None = None, *, purpose: Purpose = "USER"):
        self.__lock = Lock()
        self.__purpose = purpose or "USER"
        self.__internal_event = internal_event or TEvent()
        self.__continuations: set[Continuation] = set()

    @property
    def is_signaled(self) -> bool:
        """Indicates if the event is signaled or not.
        """
        return self.__internal_event.is_set()

    @property
    def purpose(self) -> Purpose: # pragma: no cover
        """Returns the event purpose (for testing).
        """
        return cast(Purpose, self.__purpose)

    @property
    def _internal_event(self) -> TEvent:
        return self.__internal_event # pragma: no cover


    def signal(self) -> None:
        """Signals the event.
        """
        with self.__lock:
            self.__internal_event.set()
            if self.__continuations:
                self.__notify_continuations()

    def clear(self) -> None:
        """Clears the event flag rendering it not signaled.
        """
        with self.__lock:
            self.__internal_event.clear()

    def wait(
        self,
        timeout: float | None = None, /,
        interrupt: Interrupt | None = None,
    ) -> bool:
        """Waits for the event to be signaled.

        Args:
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Returns:
            bool: A boolean value indicating if event was signaled or a timeout occurred
        """

        if interrupt is not None:
            if Event.wait_any((self,), timeout, interrupt):
                result = not interrupt.is_signaled # check if it was the event or the interrupt that was signaled
            else:
                result = False # timeout
        else:
            result = Event.__int_wait(self.__internal_event, timeout)

        if result:
            self._after_wait()
        return result


    @staticmethod
    def wait_any(
        events: Sequence[Event],
        timeout: float | None = None, /,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Waits for any of the specified events to be signaled.

        Args:
            events (Sequence[Event]): The awaited events.
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Returns:
            bool: Returns True if any of the events were signaled. Otherwise False.
        """

        if interrupt and interrupt.is_signaled:
            return False

        combined_event = Event(purpose = "CONTINUATION")

        Event._add_continuation(
            events,
            EventContinuation(
                ContinueWhen.ANY,
                events,
                combined_event,
                interrupt
            )
        )

        if Event.__int_wait(combined_event.__internal_event, timeout):
            return not interrupt or not interrupt.is_signaled
        else:
            return False


    @staticmethod
    def wait_all(
        events: Sequence[Event],
        timeout: float | None = None, /,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Waits for all of the events to be signaled

        Args:
            events (Sequence[Event]): The awaited events
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Returns:
            bool: Returns True if all of the events were signaled. Otherwise False.
        """

        if interrupt and interrupt.is_signaled:
            return False

        combined_event = Event(purpose = "CONTINUATION")

        Event._add_continuation(
            events,
            EventContinuation(
                ContinueWhen.ALL,
                events,
                combined_event,
                interrupt
            )
        )

        if Event.__int_wait(combined_event.__internal_event, timeout):
            return not interrupt or not interrupt.is_signaled
        else:
            return False

    @staticmethod
    def _add_continuation(events: Sequence[Event], continuation: Continuation) -> None:
        if continuation.interrupt and continuation.interrupt not in events:
            events = ( continuation.interrupt.wait_event, *events )

        for event in events:
            if DEBUGGING and ( debugger := get_events_debugger() ): # pragma: no cover
                debugger.register_continuation(event, continuation)

            with event.__lock:
                event.__continuations.add(continuation)
                if event.__internal_event.is_set():
                    event.__notify_continuations()


    def __notify_continuations(self) -> None:
        with self.__lock:
            expedited: list[Continuation] = []
            for continuation in self.__continuations.copy():
                try:
                    if continuation.try_continue():
                        expedited.append(continuation)

                except InterruptException:
                    expedited.append(continuation)

                finally:
                    pass

        for continuation in expedited:
            if DEBUGGING and ( debugger := get_events_debugger() ): # pragma: no cover
                debugger.unregister_continuation(self, continuation)

            with self.__lock:
                if continuation in self.__continuations: # required because events may remove continuations from other events (further down)
                    self.__continuations.remove(continuation)

        if DEBUGGING and ( debugger := get_events_debugger() ): # pragma: no cover
            debugger.unregister_continuation(self)


        for continuation in expedited:
            for continuation_event in continuation.events:
                # remove continuation on any other events
                if continuation_event is not self:
                    # use the events internal lock to avaoid task suspension
                    if continuation_event.__lock._internal_lock.acquire(timeout = 0): # pyright: ignore[reportPrivateUsage]
                        try:
                            if continuation_event.is_signaled:
                                continuation_event._after_wait()
                            if continuation in continuation_event.__continuations: # check again since continuation might have been removed before acquiring the lock
                                continuation_event.__continuations.remove(continuation)
                                if DEBUGGING and ( debugger := get_events_debugger() ): # pragma: no cover
                                    debugger.unregister_continuation(continuation_event, continuation)
                        finally:
                            continuation_event.__lock._internal_lock.release() # pyright: ignore[reportPrivateUsage]
                    else:
                        pass

        if expedited: # only trigger after_wait if any continuations were expedited
            self._after_wait()


    def _after_wait(self):
        """Overridable function called after event was awaited"""
        pass

    @staticmethod
    def __int_wait(event: TEvent, timeout: float | None = None) -> bool:
        try:
            if DEBUGGING and ( debugger := get_events_debugger() ): # pragma: no cover
                debugger.register_event_wait(event)

            if timeout and timeout < 0: # pragma: no cover
                raise ValueError("'timeout' must be a non-negative number")

            if sys.platform == "win32" and current_thread() is main_thread(): # pragma: no cover
                # as stated in https://bugs.python.org/issue35935 python cannot respond to signals
                # while awaiting events in Windows - to work around this, the waiting is done in 100ms intervals.
                start_time = time()
                while True:
                    wait = min(POLL_INTERVAL, max(0, timeout-(time()-start_time))) if timeout != None else POLL_INTERVAL
                    if event.wait(wait):
                        return True
                    elif timeout != None and (time()-start_time) >= timeout:
                        return False
            elif timeout != None and timeout <= TASK_SUSPEND_AFTER:
                return event.wait(timeout)
            else:
                if event.wait(TASK_SUSPEND_AFTER):
                    return True
                elif timeout:
                    timeout -= TASK_SUSPEND_AFTER

                from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
                with TaskScheduler.current().suspend():
                    return event.wait(timeout)

        finally:
            if DEBUGGING and ( debugger := get_events_debugger() ): # pragma: no cover
                debugger.unregister_event_wait(event)



if current_thread() is main_thread():
    # The terminate_event is set when application is requested to exit (SIGTERM or SIGINT)
    terminate_event: Annotated[Event, "An event which is signaled when application is requested to terminate"] = Event(purpose = "TERMINATE")

    def __handler(signum: int, frame: Any) -> None:
        terminate_event.signal() # pragma: no cover

    signal(SIGTERM, __handler)
    signal(SIGINT, __handler)
else:
    raise ThreadingException("Module runtime.threading.tasks must be imported (initially) in the main thread")

