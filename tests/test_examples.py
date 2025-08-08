# pyright: basic
# ruff: noqa
from pytest import raises as assert_raises, fixture

def test_example_1():

    from runtime.threading import InterruptSignal, signal_after
    from runtime.threading.tasks import Task

    def fn(task: Task[None]):
        while True:
            task.interrupt.raise_if_signaled()
            ...

    signal = InterruptSignal()
    task = Task.create(interrupt = signal.interrupt).run(fn)
    signal_after(signal, 0.1)
    task.wait()
    assert task.is_interrupted

def test_example_2():

    from runtime.threading import Event
    from runtime.threading.tasks import Task

    event = Event()

    def fn(task: Task[str], signal: Event) -> str:
        signal.wait()
        return "abc"

    task = Task.run(fn, event)

    assert not task.is_completed

    event.signal()

    assert task.result == "abc"
    assert task.is_completed

def test_example_3():

    from runtime.threading import Event, Lock
    from runtime.threading.tasks import Task

    event = Event()
    lock = Lock()
    data: dict[str, int] = { "i": 0 }

    def fn(task: Task[int], signal: Event) -> int:
        signal.wait()
        with lock:
            data["i"] += 1
            return data["i"]

    tasks = [ Task.run(fn, event) for x in range(5) ]

    event.signal()

    Task.wait_all(tasks)

    result = sum( task.result for task in tasks )

    assert result == sum(range(5+1))


def test_example_4():

    from runtime.threading import Lock, acquire_or_fail
    from runtime.threading.tasks import Task

    lock = Lock()

    with acquire_or_fail(lock, 1, lambda: Exception("Failed to acquire lock")):
        ...