from runtime.threading.core.threading_exception import ThreadingException
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.event import Event, terminate_event
from runtime.threading.core.one_time_event import OneTimeEvent
from runtime.threading.core.auto_clear_event import AutoClearEvent
from runtime.threading.core.lock import Lock
from runtime.threading.core.semaphore import Semaphore
from runtime.threading.core.helpers import acquire_or_fail, signal_after
from runtime.threading.core.interrupt_signal import InterruptSignal
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.defaults import (
    DEFAULT_PARALLELISM, TASK_SUSPEND_AFTER, TASK_KEEP_ALIVE, POLL_INTERVAL
)

def sleep(time: float, /, interrupt: Interrupt | None = None) -> None:
    terminate_event.wait(time)

__all__ = [
    'Event',
    'terminate_event',
    'OneTimeEvent',
    'AutoClearEvent',
    'Lock',
    'Semaphore',
    'ThreadingException',
    'InterruptSignal',
    'Interrupt',
    'InterruptException',
    'acquire_or_fail',
    'signal_after',
    'sleep',
    'DEFAULT_PARALLELISM',
    'TASK_SUSPEND_AFTER',
    'TASK_KEEP_ALIVE',
    'POLL_INTERVAL',
]