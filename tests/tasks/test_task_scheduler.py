# pyright: basic
from pytest import raises as assert_raises, fixture
from datetime import datetime
from typing import Any, List

from runtime.threading import ThreadingException, InterruptSignal, sleep
from runtime.threading.tasks import Task
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

from tests.shared_functions import (
    fn_interrupt_and_wait_for_task, fn_return_value, fn_return_value_after_time,
    fn_wait_until_scheduled_and_return_result
)

def test_concurrent_task_scheduler(internals):
    with ConcurrentTaskScheduler(4, 0.05) as ts:
        assert ts.max_parallelism == 4
        assert ts.suspended_threads == 0

        tasks_list: List[Task[Any]] = []
        for _ in range(10):
            t = Task.plan(fn_return_value_after_time, 0.1, "abc")
            tasks_list.append(t)
            t.schedule(ts)
            sleep(0.01)

        Task.wait_all(tasks_list)

        w_start = datetime.now()
        while ts.active_threads and (datetime.now()-w_start).total_seconds() < 5:
            sleep(0.1)

        assert ts.active_threads == 0

    with assert_raises(ThreadingException, match="Task scheduler has been closed"):
        with ConcurrentTaskScheduler(4, 0.05):
            ts.close()
            t = Task.plan(fn_return_value_after_time, 0.1, "def")
            t.schedule(ts)


def test_concurrent_task_scheduler_suspension(internals):
    with ConcurrentTaskScheduler(2, 0.05) as ts:
        sig = InterruptSignal()
        t1 = Task.plan(fn_return_value_after_time, 0.1, "ghi")

        t2 = Task.run(fn_interrupt_and_wait_for_task, sig, t1)
        sig.interrupt.wait_event.wait()
        assert t2.is_running

        t1.schedule()
        t2.wait()

def test_concurrent_task_scheduler_prioritise(internals):
    with ConcurrentTaskScheduler(2, 0.05) as ts:
        t1 = Task.create(lazy=True).plan(fn_return_value, 22)
        assert not t1.is_completed
        assert not t1.is_scheduled
        assert t1.result == 22


        def fn2(task: Task[int], other: Task[int]) -> int:
            return other.result

        t2 = Task.create(lazy=True).plan(fn_return_value, 22)
        assert not t2.is_completed
        assert not t2.is_scheduled
        t3 = Task.create(scheduler=ts).run(fn2, t2)
        assert t3.result == 22

        t4 = Task.create(lazy=True).plan(fn_return_value, 33)
        assert not t4.is_scheduled
        ts.prioritise(t4) # task will just be scheduled
        assert t4.result == 33

def test_unqueue(internals):
    with ConcurrentTaskScheduler(1) as ts:
        t1 = Task.plan(fn_return_value_after_time, 0.1, "jkl")
        t2 = Task.plan(fn_wait_until_scheduled_and_return_result, t1)

        tasks = [t1, t2]
        t2.schedule(ts)
        t1.schedule(ts) # will not run, since scheduler max parallelism = 1 and t2 is already running

        Task.wait_all(tasks)

        assert t1.is_completed
        assert t2.is_completed
