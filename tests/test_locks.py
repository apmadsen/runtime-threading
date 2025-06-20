# pyright: basic
from pytest import raises as assert_raises, fixture
from typing import Any, cast
from time import sleep
from threading import Event as IntEvent, Lock as IntLock

from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER
from runtime.threading.tasks import Task
from runtime.threading import InterruptSignal, Event, Interrupt, InterruptException, Lock, Semaphore, acquire_or_fail

from tests.shared_functions import (
    fn_acquire_signal_and_sleep, fn_signal_after_time
)

def test_lock_sync(internals):
    l1 = Lock()
    assert l1.acquire()
    assert l1.acquire()
    l1.release()
    l1.release()

    with assert_raises(RuntimeError):
        l1.release()

    l2 = Lock(False)
    signal = InterruptSignal()
    l2.acquire()
    l2.acquire(1, interrupt = signal.interrupt)
    l2.release()

    signal.signal()
    with assert_raises(InterruptException):
        l2.acquire(0.1, interrupt = signal.interrupt)


def test_semaphore_sync(internals):
    l2 = Semaphore(2)
    assert l2.acquire()
    assert l2.acquire()
    assert not l2.acquire(0)

    signal = InterruptSignal()
    signal.signal()
    with assert_raises(InterruptException):
        l2.acquire(interrupt=signal.interrupt)

    l2.release()
    l2.release()
    with assert_raises(ValueError):
        l2.release()


def test_lock_async(internals):
    l1 = Lock()
    locked_event = Event()

    Task.run(fn_acquire_signal_and_sleep, l1, locked_event, TASK_SUSPEND_AFTER+0.1)
    locked_event.wait()
    assert not l1.acquire(0)
    assert l1.acquire()

    l2 = Lock(False)
    locked_event.clear()
    signal = InterruptSignal()
    Task.run(fn_acquire_signal_and_sleep, l2, locked_event, TASK_SUSPEND_AFTER+0.1)
    locked_event.wait()
    assert l2.acquire(1, interrupt = signal.interrupt)

    # l3 = Lock(False)
    # locked_event.clear()
    # signal = InterruptSignal()
    # Task.run(lock, l3, locked_event, TASK_SUSPEND_AFTER*3)

    # Task.run(fn_signal_after_time, signal, TASK_SUSPEND_AFTER)

    # locked_event.wait()
    # with assert_raises(InterruptException):
    #     l3.acquire(TASK_SUSPEND_AFTER+0.2, interrupt = signal.interrupt)

# def test_semaphore_async(internals):
#     l1 = Semaphore()
#     locked_event = Event()

#     Task.run(fn_acquire_signal_and_sleep, l1, locked_event, TASK_SUSPEND_AFTER+0.1)
#     locked_event.wait()
#     assert not l1.acquire(0)
#     assert l1.acquire(TASK_SUSPEND_AFTER*2)


def test_lock_async_cancellation(internals):
    cs = InterruptSignal()
    l1 = Lock()
    locked_event = Event()

    Task.run(fn_acquire_signal_and_sleep, l1, locked_event, 0.1)
    locked_event.wait()
    Task.run(fn_signal_after_time, cs, 0.01)
    assert not l1.acquire(0, interrupt=cs.interrupt)
    sleep(0.05)
    with assert_raises(InterruptException):
        l1.acquire(interrupt=cs.interrupt)
    sleep(0.1)
    assert l1.acquire()

def test_acquire_or_fail(internals):
    l1 = Lock(False)
    locked_event = Event()
    int_lock = cast(IntLock, getattr(l1, "_LockBase__lock")) # requires lock to be a normal Lock (ie. "Lock(False)"), not an RLock

    with acquire_or_fail(l1, 0, lambda: Exception("Fail")):
        assert int_lock.locked()

    assert not int_lock.locked()

    Task.run(fn_acquire_signal_and_sleep, l1, locked_event, TASK_SUSPEND_AFTER+0.01)
    locked_event.wait()

    assert int_lock.locked()
    with assert_raises(Exception, match="Fail"):
        acquire_or_fail(l1, 0, lambda: Exception("Fail"))

    sleep(TASK_SUSPEND_AFTER+0.05)
    assert not int_lock.locked()
    assert acquire_or_fail(l1, 0, lambda: Exception("Fail"))

