from __future__ import annotations
import sys
from threading import Event as TEvent, current_thread, main_thread
from typing import Sequence, Any, overload, TYPE_CHECKING
from signal import signal, SIGTERM, SIGINT
from time import time

from runtime.threading.core.lock import Lock
from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER, POLL_INTERVAL
from runtime.threading.core.continuation import Continuation
from runtime.threading.core.event_continuation import EventContinuation
from runtime.threading.core.continue_when import ContinueWhen
from runtime.threading.core.threading_exception import ThreadingException
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.testing.debug import get_events_debugger

if TYPE_CHECKING:
    from runtime.threading.core.interrupt import Interrupt

DEBUGGING = False

class Event:
    """A standard event used for synchronization between tasks.
    """
    __slots__ = [ "__id", "__lock", "__internal_event", "__continuations", "__weakref__" ]

    @overload
    def __init__(self) -> None:
        """Creates a new Event.
        """
        ...
    @overload
    def __init__(self, internal_event: TEvent) -> None:
        """Creates an event from an existing internal event."""
        ...
    def __init__(self, internal_event: TEvent | None = None):
        self.__lock = Lock()
        self.__internal_event = internal_event or TEvent()
        self.__continuations: set[Continuation] = set()

    @property
    def is_signaled(self) -> bool:
        """Indicates if the underlying events flag is set or not
        """
        return self.__internal_event.is_set()

    @property
    def _internal_event(self) -> TEvent:
        return self.__internal_event # pragma: no cover


    def signal(self) -> None:
        """Signals the underlying event, bu setting its flag to True.
        """
        with self.__lock:
            self.__internal_event.set()
            if self.__continuations:
                self.__notify_continuations()

    def clear(self) -> None:
        """Clears the event flag
        """
        with self.__lock:
            self.__internal_event.clear()

    def wait(
        self,
        timeout: float | None = None, /,
        interrupt: Interrupt | None = None,
    ) -> bool:
        """Waits for the event to be signaled

        Args:
            timeout (float, optional): The timeout in seconds. Defaults to None
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

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
        """Waits for any of the events to be signaled

        Args:
            events (Sequence[Event]): The awaited events
            timeout (float, optional): The timeout in seconds. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Returns:
            bool: A boolean value indicating if any of the events were signaled or a timeout occurred
        """

        if interrupt and interrupt.is_signaled:
            return False

        combined_event = Event()

        Event.add_continuation(
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
            timeout (float, optional): The timeout in seconds. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Returns:
            bool: A boolean value indicating if any of the events were signaled or a timeout occurred
        """

        if interrupt and interrupt.is_signaled:
            return False

        combined_event = Event()

        Event.add_continuation(
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
    def add_continuation(events: Sequence[Event], continuation: Continuation) -> None:
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
                continuation_event._after_wait()
                # remove continuation on any other events as it is not done
                if continuation in continuation_event.__continuations:
                    with continuation_event.__lock:
                        if continuation in continuation_event.__continuations: # check again since continuation might have been removed before acquiring the lock
                            if DEBUGGING and ( debugger := get_events_debugger() ): # pragma: no cover
                                debugger.unregister_continuation(continuation_event, continuation)
                            continuation_event.__continuations.remove(continuation)


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
    terminate_event = Event()

    def __handler(signum: int, frame: Any) -> None:
        terminate_event.signal() # pragma: no cover

    signal(SIGTERM, __handler)
    signal(SIGINT, __handler)
else:
    raise ThreadingException("Module runtime.threading.tasks must be imported (initially) in the main thread")


