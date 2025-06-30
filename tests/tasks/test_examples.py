# pyright: basic
from pytest import raises as assert_raises, fixture
from typing import cast
from threading import Lock as TLock

from runtime.threading.core.tasks.config import TASK_SUSPEND_AFTER
from runtime.threading.tasks import Task
from runtime.threading import InterruptSignal, Event, Interrupt, InterruptException, Lock, Semaphore, acquire_or_fail, sleep

def test_example_1():

    from runtime.threading import InterruptSignal
    from runtime.threading.tasks import Task, ContinuationOptions

    try:
        signal = InterruptSignal()
        i = 227
        m = 0.78

        def fn(task: Task[float], i: float, m: float) -> float:
            task.interrupt.raise_if_signaled()
            return i * m

        def fn_continue(task: Task[float], preceding_task: Task[float], m: float) -> float:
            return preceding_task.result * m

        task1 = Task.run(fn, i, m)
        task2 = task1.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY, fn_continue, m)

        result1 = task1.result # -> 177.06
        result2 = task2.result # -> 138.1068

        assert result1 == i * m
        assert result2 == i * m * m

        task3 = Task.create(interrupt = signal.interrupt, lazy = True).plan(fn, task1.result, m)

        signal.signal()

        # task3 is run lazily when result property is accessed
        result3 = task3.result # TaskInterruptedException

    except InterruptException:
        pass


