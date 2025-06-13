# pyright: basic
from pytest import raises as assert_raises, fixture
from typing import Any, cast
from time import sleep
from threading import Event, Lock as IntLock

from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER
from runtime.threading.tasks import Lock, Semaphore, Task, InterruptSignal, TaskInterruptException, acquire_or_fail

def test_lock_sync():
    l1 = Lock()
    assert l1.acquire()
    assert l1.acquire()
    l1.release()
    l1.release()

    with assert_raises(RuntimeError):
        l1.release()

def test_semaphore_sync():
    l2 = Semaphore(2)
    assert l2.acquire()
    assert l2.acquire()
    assert not l2.acquire(0)
    l2.release()
    l2.release()
    with assert_raises(ValueError):
        l2.release()


def test_lock_async():
    def lock(task: Task[Any], lock: Lock, locked_event: Event, t: float) -> None:
        with lock:
            locked_event.set()
            sleep(t)

    l1 = Lock()
    locked_event = Event()

    Task.run(lock, l1, locked_event, TASK_SUSPEND_AFTER+0.1)
    locked_event.wait()
    assert not l1.acquire(0)
    assert l1.acquire()


def test_semaphore_async():
    def lock(task: Task[Any], lock: Semaphore, locked_event: Event, t: float) -> None:
        with lock:
            locked_event.set()
            sleep(t)

    l1 = Semaphore()
    locked_event = Event()

    Task.run(lock, l1, locked_event, TASK_SUSPEND_AFTER+0.1)
    locked_event.wait()
    assert not l1.acquire(0)
    assert l1.acquire()


def test_lock_async_cancellation():
    cs = InterruptSignal()
    def lock(task: Task[Any], lock: Lock, locked_event: Event, t: float) -> None:
        with lock:
            # print("lock")
            locked_event.set()
            sleep(t)
        # print("unlock")

    def cancel_after(task: Task[Any], cs: InterruptSignal, t: float) -> None:
        sleep(t)
        cs.signal()
        # print("cancel")


    l1 = Lock()
    locked_event = Event()

    Task.run(lock, l1, locked_event, 0.1)
    locked_event.wait()
    Task.run(cancel_after, cs, 0.01)
    assert not l1.acquire(0, interrupt=cs.interrupt)
    sleep(0.05)
    with assert_raises(TaskInterruptException):
        l1.acquire(interrupt=cs.interrupt)
    sleep(0.1)
    assert l1.acquire()





def test_acquire_or_fail():
    def lock(task: Task[Any], lock: Lock, locked_event: Event, t: float) -> None:
        with lock:
            locked_event.set()
            sleep(t)

    l1 = Lock(False)
    locked_event = Event()
    int_lock = cast(IntLock, getattr(l1, "_Lock__lock")) # requires lock to be a normal Lock (ie. "Lock(False)"), not an RLock

    with acquire_or_fail(l1, 0, lambda: Exception("Fail")):
        assert int_lock.locked()

    assert not int_lock.locked()

    Task.run(lock, l1, locked_event, TASK_SUSPEND_AFTER+0.01)
    locked_event.wait()

    assert int_lock.locked()
    with assert_raises(Exception):
        acquire_or_fail(l1, 0, lambda: Exception("Fail"))

    sleep(TASK_SUSPEND_AFTER+0.05)
    assert not int_lock.locked()
    assert acquire_or_fail(l1, 0, lambda: Exception("Fail"))

