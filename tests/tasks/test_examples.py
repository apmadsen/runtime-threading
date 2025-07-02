# pyright: basic
from pytest import raises as assert_raises, fixture

def test_example_1():

    from runtime.threading import InterruptSignal, InterruptException
    from runtime.threading.tasks import Task

    try:
        signal = InterruptSignal()
        i = 227
        m = 0.78

        def fn(task: Task[float], i: float, m: float) -> float:
            task.interrupt.raise_if_signaled()
            return i * m

        task = Task.create(interrupt = signal.interrupt, lazy = True).run(fn, i, m)

        result = task.result # -> 177.06

        assert result == i * m

    except InterruptException:
        pass


def test_example_2():

    from runtime.threading.tasks import Task, ContinuationOptions

    i = 227
    m = 0.78

    def fn(task: Task[float], i: float, m: float) -> float:
        return i * m

    def fn_continue(task: Task[float], preceding_task: Task[float], m: float) -> float:
        return preceding_task.result * m

    task1 = Task.run(fn, i, m)
    task2 = task1.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY, fn_continue, m)

    result1 = task1.result # -> 177.06
    result2 = task2.result # -> 138.1068

    assert result1 == i * m
    assert result2 == i * m * m

def test_example_3():

    from typing import Sequence
    from runtime.threading.tasks import Task, ContinuationOptions

    i = 227
    m = 0.78

    def fn(task: Task[float], i: float, m: float) -> float:
        return i * m

    def fn_continue(task: Task[float], preceding_tasks: Sequence[Task[float]]) -> float:
        return sum(( task.result for task in preceding_tasks ))

    tasks = [ Task.run(fn, i, m) for x in range(5) ]
    task = Task.with_all(tasks, ContinuationOptions.DEFAULT).run(fn_continue)


    result = task.result # -> 885.3

    assert result == i * m * 5

def test_example_4():

    from runtime.threading.tasks import Task

    task = Task.from_result("abc") # -> Task[str]
    result = task.result # -> "abc"

    assert result == "abc"

def test_example_5():

    from runtime.threading.tasks import Task
    from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

    def fn(task: Task[str]) -> str:
        return "abc"

    with ConcurrentTaskScheduler(8) as scheduler:
        task = Task.create(scheduler = scheduler).run(fn)

    result = task.result # -> "abc"

    assert result == "abc"

