# pyright: basic
from pytest import raises as assert_raises, fixture
from typing import Any, Iterable, Sequence, TypeVar
from time import sleep
from re import escape

from runtime.threading.tasks import (
    Task, ContinuationOptions, schedulers, AggregateException, TaskState, TaskException,
    TaskCompletedError, TaskNotScheduledError, TaskAlreadyRunningError, TaskAlreadyScheduledError,
    TaskCanceledError
)
from runtime.threading import InterruptSignal, Interrupt, InterruptException, Event


T = TypeVar('T')

def test_basic():
    t1 = Task.create().future(do_something, 0.025)
    t1 = Task.future(do_something, 0.025)

    with assert_raises(TaskException, match=escape(str(TaskNotScheduledError))):
        t1.result

    t2 = Task.run(do_something, 0.03)
    assert t1.id != t2.id
    t1.schedule()

    with assert_raises(TaskException, match=escape(str(TaskAlreadyScheduledError))):
        t1.schedule()



    assert not Task.wait_all([t1, t2], timeout=0.01)
    assert Task.wait_any([t1, t2])
    assert Task.wait_all([t1, t2])
    assert t1.wait()
    assert t1.is_completed_successfully

    with assert_raises(TaskException, match=escape(str(TaskCompletedError))):
        t1.schedule()


    def fn_task(task: Task[Any]) -> Task[Any] | None:
        return task.current()

    t3 = Task.run(fn_task)
    assert t3.result is t3

    def fn_parent(task: Task[Any]) -> Task[Any] | None:
        assert task.current()
        def fn_child(task: Task[Any]) -> Task[Any] | None:
            return task.parent
        return Task.run(fn_child).result

    tparent = Task.run(fn_parent)
    assert tparent.result is tparent

def test_run_synchronously():
    signal1 = Event()
    def fn_wait_for(task: Task[Any], signal: Interrupt):
        signal1.set()
        Event.wait_any((task.interrupt.wait_event, signal.wait_event))


    signal2 = InterruptSignal()
    t1 = Task.run(fn_wait_for, signal2.interrupt)
    signal1.wait() # needed to avoid deadlock

    with assert_raises(TaskException, match=escape(str(TaskAlreadyRunningError))):
        t1.run_synchronously()

    signal2.signal()

    t1.wait()
    assert t1.is_completed

    with assert_raises(TaskException, match=escape(str(TaskCompletedError))):
        t1.run_synchronously()


    t2 = Task.future(do_something, 0.025)
    t2.cancel()

    with assert_raises(TaskException, match=escape(str(TaskCanceledError))):
        t2.run_synchronously()


def test_suspend():
    with schedulers.ConcurrentTaskScheduler(1) as scheduler:
        # t2 should suspend while waiting for t1 to complete,
        # which should allow t3 to run and start t1, which in turn
        # lets t2 complete

        t1 = Task.future(do_something, 0.025)

        def do_wait(task: Task[Any], t: Task[Any]) -> None:
            sleep(0.01)
            t.wait()

        t2 = Task.create(scheduler=scheduler).run(do_wait, t1)

        def do_start(task: Task[Any], t: Task[Any]) -> None:
            sleep(0.1)
            t.schedule(scheduler)

        t3 = Task.create(scheduler=scheduler).run(do_start, t1)

        t2.wait()
        sleep(scheduler.keep_alive + 0.1)

    assert scheduler.active_threads == 0


def test_generic():
    test_str = "test"
    t = Task.future(do_something_gen, 0.05, test_str)
    t.schedule()
    t.wait()
    assert t.result == test_str

def test_exceptions():
    t1 = Task.future(do_something_fail, 0.05)
    t2 = Task.future(do_something, 0.1)
    t1.schedule()
    t2.schedule()

    with assert_raises(Exception, match="Task fail"):
        t1.result
    with assert_raises(AggregateException):
        Task.wait_all([t1, t2])

def test_cancellation():
    cs1 = InterruptSignal()
    cs2 = InterruptSignal()
    t1 = Task.create(interrupt=cs1.interrupt).future(do_something_or_cancel, 5, 0.05)
    t2 = Task.create(interrupt=cs2.interrupt).future(do_something, 0.1)
    t1.schedule()
    cs1.signal()
    t2.schedule()
    sleep(0.06)
    cs2.signal()

    with assert_raises(InterruptException):
        t1.result

    t1.wait()
    assert t1.is_canceled

    t2.wait()
    assert not t2.is_canceled
    try:
        Task.wait_all([t1, t2])
    except AggregateException as ex:
        ex.handle(lambda e: isinstance(e, InterruptException))


    def fn(task: Task[Any]):
        sig = InterruptSignal()
        sig.signal()
        sig.interrupt.raise_if_signaled()

    t3 = Task.run(fn)
    t3.wait()
    assert t3.is_failed

    signal1 = Event()
    def fn_wait_for(task: Task[Any], signal: Interrupt):
        signal1.set()
        Event.wait_any((task.interrupt.wait_event, signal.wait_event))
        task.interrupt.raise_if_signaled()



    signal3 = InterruptSignal()
    t3 = Task.run(fn_wait_for, signal3.interrupt)
    signal1.wait()
    t3.cancel()
    t3.wait()
    assert t3.is_canceled


# def test_linked_cancellation():
#     # when running a tasked with linked interrupts, signaling of any of those linked interrupts
#     # should result in task being canceled

#     def fn_task_1(task: Task[Any]) -> int:
#         task.interrupt.wait_event.wait()
#         task.interrupt.raise_if_signaled()
#         return 0

#     task1 = Task.run(fn_task_1)

#     def fn_task_2(task: Task[Any]) -> int:
#         return task1.result

#     task2 = Task.run(fn_task_2)
#     task1.cancel()

#     with assert_raises(TaskInterruptException):
#         task2.result

#     assert task2.is_canceled
#     assert task2.state == TaskState.CANCELED

def test_continuations():
    # assertions on task start and finish time, based on time.sleep is risky,
    # since starting time isn't guaranteed on sceduler and internal events
    # might not react as fast as the test requires

    test_str = "test"
    t1 = Task.future(do_something_gen, 0.005, test_str)
    t2 = t1.continue_with(ContinuationOptions.DEFAULT, continue_something)
    t3 = t2.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.ON_CANCELED, continue_something)
    _ = t3.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE, continue_something)
    t4 = t1.continue_with(ContinuationOptions.DEFAULT, continue_something_with_arg, 45, y=2)
    t1.schedule()

    cs5 = InterruptSignal()
    t5 = Task.create(interrupt=cs5.interrupt).future(do_something_gen, 0.05, test_str)
    t6 = t5.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY, continue_something)
    t7 = t5.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.ON_CANCELED, continue_something)
    t5.schedule()
    sleep(0.001)
    cs5.signal()
    sleep(.05)
    t7.wait()

    assert t4.result.endswith(" "+str(45*2))
    with assert_raises(InterruptException):
        get_result(t6) # t6 is implicitly canceled and will throw an exception


    t8 = Task.future(do_something_gen, 0.01, "Task 8 done")
    t9 = Task[str].future(do_something_gen, 0.001, "Task 9 done")
    t10 = Task.with_any([t8, t9]).then(get_result1)
    t11 = Task.with_all([t8, t9]).then(get_result1)
    t14 = Task.with_all([t8, t9]).then(get_result1_with_args, 2)
    t8.schedule()
    t9.schedule()
    Task.wait_all([t10, t11])


    assert t10.result in ("Task 8 done", "Task 9 done")
    assert t11.result == "Task 8 done"
    assert t14.result == 4

    t13 = Task.wait_all([t10, t11])
    t12 = Task.wait_all([
        Task.run(do_something_gen, 0.01, "Task 121 done"),
        Task.run(do_something_gen, 0.03, "Task 122 done"),
        Task.run(do_something_gen, 0.02, "Task 123 done"),
        Task.run(do_something_gen, 0.001, "Task 124 done"),
    ])

    def fn_fail(task: Task[str]) -> str:
        raise Exception

    t14 = Task.run(fn_fail)
    # t15 = Task.run(fn_fail)
    assert t14.continue_with(ContinuationOptions.ON_FAILED, continue_something).result == "Failed"

    # Task.wait_any((t14,t15))


def test_lazy_task():
    test_str = "test"
    t1 = Task.create(lazy=True).future(do_something_gen, 0.005, test_str)
    t2 = Task.create(lazy=True).future(do_something_gen, 0.005, test_str)
    assert not t1.is_scheduled
    assert not t1.is_completed
    assert t1.is_lazy

    result = t1.result # will be scheduled and run in the default scheduler
    assert t1.is_completed
    assert result == test_str

    result = Task.run(continue_something, t2).result
    assert t2.is_completed
    assert result == test_str


    # t2 = Task.future(do_something_gen, 0.005, test_str, lazy=True)
    # def fn_t1(task: Task[Any]) -> str:
    #     return t2.result
    # result = Task.invoke(fn_t1).result
    x=0


def get_result(i: Task[T]) -> T:
    return i.result


def get_result1(task: Task[str], tasks: Iterable[Task[str]]) -> str:
    # print(str(len(list(tasks))) + " finished tasks")
    return list(map(lambda t: t.result, filter(lambda t: t.is_completed, tasks)))[0]

def get_result1_with_args(task: Task[int], tasks: Sequence[Task[Any]], x: int) -> int:
    return len(tasks) * x

def do_something(task: Task[Any], s: float) -> None:
    task.interrupt.raise_if_signaled()
    # print("sync task start")
    sleep(s)
    # print("sync task done")


def do_something_fail(task: Task[Any], s: float) -> None:
    sleep(s)
    raise Exception("Task fail")

def do_something_gen(task: Task[str], s: float, r: str) -> str:
    sleep(s)
    task.interrupt.raise_if_signaled()
    # print("task done : " + current_thread().name)
    return r


def continue_something(task: Task[str], i: Task[str]) -> str:
    if i.is_canceled:
        # print("continuation done from canceled : " + current_thread().name)
        return "Canceled"
    if i.is_failed:
        # print("continuation done from canceled : " + current_thread().name)
        return "Failed"
    else:
        # print("continuation done from completed: " + current_thread().name)
        return i.result

def continue_something_with_arg(task: Task[str], i: Task[str], x: int, *, y: int) -> str:
    if i.is_canceled:
        # print("continuation done from canceled : " + current_thread().name)
        return "Canceled" + " " + str(x*y)
    else:
        # print("continuation done from completed: " + current_thread().name)
        return i.result + " " + str(x*y)

def do_something_or_cancel(task: Task[Any], o: int, s: int|float):
    for _ in range(o):
        sleep(s)
        task.interrupt.raise_if_signaled()


