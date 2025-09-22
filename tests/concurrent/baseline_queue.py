from typing import Iterable, Any
from datetime import datetime
from queue import Queue as OrgQueue, Empty as QueueEmptyException

from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler
from runtime.threading.tasks import Task, ContinuationOptions
from runtime.threading import InterruptSignal, Interrupt
from runtime.threading.concurrent import Queue

def baseline_queue():
    count = 10000

    for parallelism_in in [2,4,8]:
        with ConcurrentTaskScheduler(parallelism_in) as scheduler_in:
            facit = sorted([ i for i in range(count) ] * parallelism_in)

            for parallelism_out in [2,4,8]:
                print("Queue comparison @ in: %d out: %d" % (parallelism_in, parallelism_out))

                ### runtime.threading.tasks.concurrent.queue ###

                with ConcurrentTaskScheduler(parallelism_out) as scheduler_out:
                    queue1 = Queue[int]()
                    cts1 = InterruptSignal()
                    ts = datetime.now()

                    tasks1 = [ Task.create(scheduler=scheduler_out).run(fn_concurrent_queue, queue1, cts1.interrupt) for _ in range(parallelism_out) ]

                    def put1(task: Task[Any]):
                        for i in range(count):
                            queue1.enqueue(i)

                    def put1done(task: Task[Any], tasks: Iterable[Task[Any]]):
                        cts1.signal()

                    Task.with_all([
                        Task.create(scheduler=scheduler_in).run(put1) for _ in range(parallelism_in)
                    ], options=ContinuationOptions.DEFAULT).run(put1done)
                    Task.wait_all(tasks1)

                    t1 = datetime.now()-ts
                    result1: list[int] = []
                    for task in tasks1:
                        result1 += task.result

                    result1 = sorted(result1)
                    assert facit == result1
                    print("New Queue: %s" % t1)

                    ### builtin python queue ###

                    queue2: 'OrgQueue[int]' = OrgQueue()
                    cts2 = InterruptSignal()
                    ts = datetime.now()
                    tasks2 = [ Task.create(scheduler=scheduler_out).run(fn_org_queue, queue2, cts2.interrupt) for _ in range(parallelism_out) ]

                    def put2(task: Task[Any]):
                        for i in range(count):
                            queue2.put_nowait(i)

                    def put2done( task: Task[Any], tasks: Iterable[Task[Any]]):
                        cts2.signal()

                    Task.with_all([
                        Task.create(scheduler=scheduler_in).run(put2) for _ in range(parallelism_in)
                    ], options=ContinuationOptions.DEFAULT).run(put2done)
                    Task.wait_all(tasks2)

                    t2 = datetime.now()-ts
                    result2: list[int] = []
                    for task in tasks2:
                        result2 += task.result

                    result2 = sorted(result2)
                    assert facit == result2
                    print("Builtin Queue: %s" % t2)

                    if t2 > t1:
                        print("Difference: -- %f\n" % (t1-t2).total_seconds())
                    else:
                        print("Difference: ++ %f\n" % (t1-t2).total_seconds())

                    assert result1 == result2


def fn_concurrent_queue(task: Task[list[int]], queue: Queue[int], interrupt: Interrupt) -> list[int]:
    results: list[int] = []
    while True:
        result, success = queue.try_dequeue(0.01, interrupt=task.interrupt)
        if success and result is not None:
            results.append(result)
        elif interrupt.is_signaled:
            break
    return results

def fn_org_queue(task: Task[list[int]], queue: 'OrgQueue[int]', interrupt: Interrupt) -> list[int]:
    results: list[int] = []
    while True:
        try:
            result = queue.get(timeout=0.01)
            queue.task_done()
            results.append(result)
        except QueueEmptyException:
            if interrupt.wait_event.wait(0.01):
                break
    return results

if __name__ == "__main__":
    baseline_queue()