from runtime.threading.core.auto_clear_event import AutoClearEvent
from runtime.threading.core.defaults import (
    DEFAULT_PARALLELISM,
    POLL_INTERVAL,
    TASK_KEEP_ALIVE,
    TASK_SUSPEND_AFTER,
)
from runtime.threading.core.event import Event, terminate_event
from runtime.threading.core.helpers import acquire_or_fail, signal_after
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.interrupt_signal import InterruptSignal
from runtime.threading.core.lock import Lock
from runtime.threading.core.one_time_event import OneTimeEvent
from runtime.threading.core.semaphore import Semaphore
from runtime.threading.core.synclock import synclock
from runtime.threading.core.threading_exception import ThreadingException


def sleep(time: float, /, interrupt: Interrupt | None = None) -> None:
    terminate_event.wait(time)

__all__ = [
    'DEFAULT_PARALLELISM',
    'POLL_INTERVAL',
    'TASK_KEEP_ALIVE',
    'TASK_SUSPEND_AFTER',
    'AutoClearEvent',
    'Event',
    'Interrupt',
    'InterruptException',
    'InterruptSignal',
    'Lock',
    'OneTimeEvent',
    'Semaphore',
    'ThreadingException',
    'acquire_or_fail',
    'signal_after',
    'sleep',
    'synclock',
    'terminate_event',
]