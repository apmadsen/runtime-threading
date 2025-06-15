from __future__ import annotations
import sys
from threading import Event as TEvent, current_thread, main_thread
from typing import Sequence, MutableSequence, Any
from signal import signal, SIGTERM, SIGINT
from datetime import datetime
from weakref import WeakKeyDictionary

from runtime.threading.core.lock import Lock
from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER, POLL_INTERVAL
from runtime.threading.core.tasks.event_continuation import EventContinuation
from runtime.threading.core.tasks.continue_when import ContinueWhen
from runtime.threading.core.threading_exception import ThreadingException


LOCK = Lock()
CONTINUATIONS: WeakKeyDictionary[Event, MutableSequence[EventContinuation]] = WeakKeyDictionary()

class Event:
    """A standard event used for synchronization between tasks.
    """
    __slots__ = [ "__internal_event", "__weakref__" ]

    def __init__(self):
        """Creates a new Event.
        """
        self.__internal_event = TEvent()


    @property
    def is_set(self) -> bool:
        """Indicates if the event flag is ser or not
        """
        return self.__internal_event.is_set()

    def set(self) -> None:
        """Sets the event flag to True
        """
        self.__internal_event.set()
        Event.__notify_continuations(self)

    def clear(self) -> None:
        """Clears the event flag
        """
        self.__internal_event.clear()

    def wait(self, timeout: float | None=None) -> bool:
        """Waits for the event to be set

        Args:
            timeout (float, optional): The timeout in seconds. Defaults to None

        Returns:
            bool: A boolean value indicating if event was set or a timeout occurred
        """
        result = Event.__int_wait(self.__internal_event, timeout)
        if result:
            self._after_wait()
        return result


    @classmethod
    def wait_any(cls, events: Sequence[Event], timeout: float | None = None) -> bool:
        """Waits for any of the events to be set

        Args:
            events (Sequence[Event]): The awaited events
            timeout (float, optional): The timeout in seconds. Defaults to None.

        Returns:
            bool: A boolean value indicating if any of the events were set or a timeout occurred
        """
        combined_event = TEvent()
        Event.__add_continuation(events, EventContinuation(ContinueWhen.ANY, events, combined_event))

        return Event.__int_wait(combined_event, timeout)


    @classmethod
    def wait_all(cls, events: Sequence[Event], timeout: float | None = None) -> bool:
        """Waits for all of the events to be set

        Args:
            events (Sequence[Event]): The awaited events
            timeout (float, optional): The timeout in seconds. Defaults to None.

        Returns:
            bool: A boolean value indicating if any of the events were set or a timeout occurred
        """
        combined_event = TEvent()
        Event.__add_continuation(events, EventContinuation(ContinueWhen.ALL, events, combined_event))
        return Event.__int_wait(combined_event, timeout)


    @classmethod
    def __add_continuation(cls, events: Sequence[Event], continuation: EventContinuation) -> None:
        with LOCK:
            already_set: Sequence[Event] = []
            for event in events:
                if event.is_set:
                    already_set.append(event)

                if event not in CONTINUATIONS:
                    CONTINUATIONS[event] = [continuation]
                else:
                    CONTINUATIONS[event].append(continuation)

            for event in already_set:
                Event.__notify_continuations(event)


    @classmethod
    def __notify_continuations(cls, event: Event) -> None:
        with LOCK:
            if event in CONTINUATIONS:
                expedited: MutableSequence[EventContinuation] = []

                for continuation in list(CONTINUATIONS[event]):
                    if continuation.try_continue():
                        expedited.append(continuation)
                        CONTINUATIONS[event].remove(continuation)

                for continuation in expedited:
                    for continuation_event in continuation.events:
                        continuation_event._after_wait()
                        if continuation_event in CONTINUATIONS:
                            if continuation in CONTINUATIONS[continuation_event]:
                                CONTINUATIONS[continuation_event].remove(continuation)

                            if len(CONTINUATIONS[continuation_event]) == 0:
                                del CONTINUATIONS[continuation_event]

    def _after_wait(self):
        """Overridable function called after event was awaited"""
        pass



    @classmethod
    def __int_wait(cls, event: TEvent, timeout: float | None = None) -> bool:
        if timeout and timeout < 0: # pragma: no cover
            raise ValueError("'timeout' must be a non-negative number")

        if sys.platform == "win32" and current_thread() is main_thread():
            # as stated in https://bugs.python.org/issue35935 python cannot respond to signals
            # while awaiting events in Windows - to work around this, the waiting is done in 100ms intervals.
            start_time = datetime.now()
            while True:
                wait = min(POLL_INTERVAL, max(0, timeout-(datetime.now()-start_time).total_seconds())) if timeout != None else POLL_INTERVAL
                if event.wait(wait):
                    return True
                elif timeout != None and (datetime.now()-start_time).total_seconds() >= timeout:
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


if current_thread() is main_thread():
    # The terminate_event is set when application is requested to exit (SIGTERM or SIGINT)
    terminate_event = Event()

    def __handler(signum: int, frame: Any) -> None:
        terminate_event.set() # pragma: no cover

    signal(SIGTERM, __handler)
    signal(SIGINT, __handler)
else:
    raise ThreadingException("Module runtime.threading.tasks must be imported (initially) in the main thread")


