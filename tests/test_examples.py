# pyright: basic
from pytest import raises as assert_raises, fixture
from typing import cast
from threading import Lock as TLock

from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER
from runtime.threading.tasks import Task
from runtime.threading import InterruptSignal, Event, Interrupt, InterruptException, Lock, Semaphore, acquire_or_fail, sleep

def test_signal_after():

    from typing import Any
    from runtime.threading import InterruptSignal, signal_after
    from runtime.threading.tasks import Task

    def fn(task: Task[Any]):
        while True:
            task.interrupt.raise_if_signaled()
            ...

    signal = InterruptSignal()
    task = Task.create(interrupt = signal.interrupt).run(fn)
    signal_after(signal, 0.1)
    task.wait()
    assert task.is_interrupted
