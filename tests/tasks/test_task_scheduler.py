# pyright: basic
from pytest import raises as assert_raises, fixture
from time import sleep
from datetime import datetime
from typing import Any, List

from runtime.threading.tasks import Task
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

def test_scheduler():
    with ConcurrentTaskScheduler(4, 0.05) as ts:
        tasks: List[Task[Any]] = []
        for _ in range(10):
            t = Task.future(do_something, 0.1)
            # print("Task 'Task_" + str(t.id) + " queued")
            tasks.append(t)
            t.schedule(ts)
            sleep(0.01)

        Task.wait_all(tasks)

        w_start = datetime.now()
        while ts.active_threads and (datetime.now()-w_start).total_seconds() < 5:
            sleep(0.1)

        assert ts.active_threads == 0

# def test_unqueue():
#     with ConcurrentTaskScheduler(1) as ts:
#         t1 = Task.future(do_something, 0.1)
#         t2 = Task.future(wait_for, t1)

#         tasks = [t1, t2]
#         t2.schedule(ts)
#         t1.schedule(ts) # will not run, since scheduler max parallelism = 1 and t2 is already running

#         Task.wait_all(tasks)

#         assert t1.is_completed
#         assert t2.is_completed
#         x=0


def do_something(task: Task[float], s: float) -> float:
    sleep(s)
    # print("Task '" + str(current_thread().name) + "' done")
    return 10

def wait_for(task: Task[float], t: Task[float]):
    while not t.is_scheduled:
        sleep(0.1)
    return t.result # this will unqueue task t and run it synchronously



