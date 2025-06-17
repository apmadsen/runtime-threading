# pyright: basic
from pytest import raises as assert_raises, fixture
from time import sleep
from datetime import datetime
from typing import Any, List

from runtime.threading import ThreadingException, InterruptSignal
from runtime.threading.tasks import Task
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

def test_concurrent_task_scheduler():
    with ConcurrentTaskScheduler(4, 0.05) as ts:
        assert ts.max_parallelism == 4
        assert ts.suspended_threads == 0

        tasks: List[Task[Any]] = []
        for _ in range(10):
            t = Task.future(do_something, 0.1)
            tasks.append(t)
            t.schedule(ts)
            sleep(0.01)

        Task.wait_all(tasks)

        w_start = datetime.now()
        while ts.active_threads and (datetime.now()-w_start).total_seconds() < 5:
            sleep(0.1)

        assert ts.active_threads == 0

    with assert_raises(ThreadingException, match="Task scheduler has been closed"):
        ts = ConcurrentTaskScheduler(4, 0.05)
        ts.close()
        t = Task.future(do_something, 0.1)
        t.schedule(ts)


def test_concurrent_task_scheduler_suspension():
    with ConcurrentTaskScheduler(2, 0.05) as ts:
        sig = InterruptSignal()
        t1 = Task.future(do_something, 0.1)

        def fn(task: Task[Any], other: Task[Any]):
            sig.signal()
            other.wait()

        t2 = Task.run(fn, t1)
        sig.interrupt.wait_event.wait()
        assert t2.is_running

        t1.schedule()
        t2.wait()

def test_concurrent_task_scheduler_prioritise():
    with ConcurrentTaskScheduler(2, 0.05) as ts:
        def fn(task: Task[int]) -> int:
            return 22

        t1 = Task.create(lazy=True).future(fn)
        assert not t1.is_completed
        assert not t1.is_scheduled
        assert t1.result == 22


        def fn2(task: Task[int], other: Task[int]) -> int:
            return other.result

        t2 = Task.create(lazy=True).future(fn)
        assert not t2.is_completed
        assert not t2.is_scheduled
        t3 = Task.create(scheduler=ts).run(fn2, t2)
        assert t3.result == 22

        t4 = Task.create(lazy=True).future(fn)
        assert not t4.is_scheduled
        ts.prioritise(t4) # task will just be scheduled
        assert t4.result == 22

def test_unqueue():
    with ConcurrentTaskScheduler(1) as ts:
        t1 = Task.future(do_something, 0.1)
        t2 = Task.future(wait_for, t1)

        tasks = [t1, t2]
        t2.schedule(ts)
        t1.schedule(ts) # will not run, since scheduler max parallelism = 1 and t2 is already running

        Task.wait_all(tasks)

        assert t1.is_completed
        assert t2.is_completed
        x=0


def do_something(task: Task[float], s: float) -> float:
    sleep(s)
    # print("Task '" + str(current_thread().name) + "' done")
    return 10

def wait_for(task: Task[float], t: Task[float]):
    while not t.is_scheduled:
        sleep(0.1)
    return t.result # this will unqueue task t and run it synchronously



