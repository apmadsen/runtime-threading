# pyright: basic
from typing import Iterable, Any, cast

from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler
from runtime.threading.tasks import Task, ContinuationOptions
from runtime.threading import InterruptSignal, Interrupt
from runtime.threading.concurrent import Queue

def test_basics(internals):
    queue = Queue[int]()
    facit = [ i for i in range(5) ]

    for i in facit:
        queue.enqueue(i)

    result: list[int] = []

    while dequeued := queue.try_dequeue():
        if dequeued[1]:
            result.append(cast(int, dequeued[0]))
        else:
            break

    assert result == facit

    for i in result:
        queue.requeue(i)

    result.clear()

    while dequeued := queue.try_dequeue():
        if dequeued[1]:
            result.append(cast(int, dequeued[0]))
        else:
            break

    assert result == list(reversed(facit))


def test_queue(internals):
    count = 100

    for parallelism_in in [2,4,8]:
        with ConcurrentTaskScheduler(parallelism_in) as scheduler_in:
            facit = sorted([ i for i in range(count) ] * parallelism_in)

            for parallelism_out in [2,4]:

                with ConcurrentTaskScheduler(parallelism_out) as scheduler_out:
                    queue1 = Queue[int]()
                    cts1 = InterruptSignal()

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


                    result1: list[int] = []
                    for task in tasks1:
                        result1 += task.result

                    result1 = sorted(result1)
                    assert facit == result1


def fn_concurrent_queue(task: Task[list[int]], queue: Queue[int], interrupt: Interrupt) -> list[int]:
    results: list[int] = []
    while True:
        result, success = queue.try_dequeue(interrupt=task.interrupt)
        if success and result != None:
            results.append(result)
        elif interrupt.is_signaled:
            break
    return results
