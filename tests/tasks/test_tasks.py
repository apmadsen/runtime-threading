# pyright: basic
# ruff: noqa
from pytest import raises as assert_raises, fixture
from typing import Any, Iterable, Sequence, TypeVar
from typingutils import get_type_name
from re import escape

from runtime.threading.tasks import (
    Task, ContinuationOptions, schedulers, AggregateException, TaskState, TaskException,
    TaskCompletedError, TaskNotScheduledError, TaskAlreadyRunningError, TaskAlreadyScheduledError,
    AwaitedTaskInterruptedError
)
from runtime.threading.tasks.schedulers import TaskScheduler, ConcurrentTaskScheduler
from runtime.threading import InterruptSignal, Interrupt, InterruptException, Event, sleep

from tests.shared_functions import (
    fn_return_parent_task, fn_return_task, fn_wait_for_signal, fn_schedule_task_after_time,
    fn_wait_for_task_after_time, fn_raise_unrelated_signal, fn_fail_immediately, fn_raise_interrupt,
    fn_get_first_result_from_tasks, fn_get_count_of_tasks, fn_sleep_if_not_interrupted,
    fn_fail_after_time, fn_return_value_after_time, fn_raise_interrupt_after_time,
    fn_continue_and_return_result_or_state, fn_continue_and_return_result_or_state_with_mods
)


T = TypeVar('T')


def test_basic(internals):
    t1 = Task.plan(fn_sleep_if_not_interrupted, 0.5)

    with assert_raises(TaskException, match=escape(str(TaskNotScheduledError))):
        t1.result

    t2 = Task.run(fn_sleep_if_not_interrupted, 0.5)
    assert t1.id != t2.id
    t1.schedule()

    with assert_raises(TaskException, match=escape(str(TaskAlreadyScheduledError))):
        t1.schedule()

    assert not Task.wait_all([t1, t2], 0.0001)
    assert Task.wait_any([t1, t2])
    assert Task.wait_all([t1, t2])
    assert t1.wait()
    assert t1.is_completed_successfully

    with assert_raises(TaskException, match=escape(str(TaskCompletedError))):
        t1.schedule()


    t3 = Task.run(fn_return_task)
    assert t3.result is t3

    tparent = Task.run(fn_return_parent_task)
    assert tparent.result is tparent
    # Task.wait_all((t1, t2, t3))

# def test_x(internals):
#     # t1 = Task.plan(fn_sleep_if_not_interrupted, 0.5)
#     t2 = Task.run(fn_sleep_if_not_interrupted, 0.5)
#     # t1.schedule()

#     # Task.wait_all([t1, t2])
#     t2.wait()


def test_run_synchronously(internals):
    signal1 = Event()
    signal2 = InterruptSignal()
    signal3 = InterruptSignal()
    t1 = Task.run(fn_wait_for_signal, signal2.interrupt, signal1)
    signal1.wait() # needed to avoid deadlock

    with assert_raises(TaskException, match=escape(str(TaskAlreadyRunningError))):
        t1.run_synchronously()

    signal2.signal()

    t1.wait()
    assert t1.is_completed

    with assert_raises(TaskException, match=escape(str(TaskCompletedError))):
        t1.run_synchronously()


def test_suspend(internals):
    with schedulers.ConcurrentTaskScheduler(1) as scheduler:
        # t2 should suspend while waiting for t1 to complete,
        # which should allow t3 to run and start t1, which in turn
        # lets t2 complete

        t1 = Task.plan(fn_sleep_if_not_interrupted, 0.025)
        t2 = Task.create(scheduler=scheduler).run(fn_wait_for_task_after_time, t1, 0.01)
        t3 = Task.create(scheduler=scheduler).run(fn_schedule_task_after_time, t1, scheduler, 0.1)

        t2.wait()
        sleep(scheduler.keep_alive + 0.1)

    assert scheduler.active_threads == 0
    assert scheduler.suspended_threads == 0


def test_generic(internals):
    test_str = "test"
    t = Task.plan(fn_return_value_after_time, 0.05, test_str)
    t.schedule()
    t.wait()
    assert t.result == test_str

def test_exceptions(internals):
    t1 = Task.run(fn_fail_after_time, 0.05, "Task fail")
    t2 = Task.run(fn_sleep_if_not_interrupted, 0.1)
    t3 = Task.run(fn_fail_immediately, "Task fail")

    with assert_raises(Exception, match="Task fail"):
        t1.result

    with assert_raises(Exception, match="Task fail"):
        t3.result

    with assert_raises(AggregateException):
        Task.wait_all([t1, t2])

def test_interruption(internals):
    cs1 = InterruptSignal()
    cs2 = InterruptSignal()
    t1 = Task.create(interrupt=cs1.interrupt).plan(fn_raise_interrupt_after_time, 0.01)
    t2 = Task.create(interrupt=cs2.interrupt).plan(fn_sleep_if_not_interrupted, 0.01)
    t1.schedule()
    cs1.signal()
    t2.schedule()
    sleep(0.06)
    cs2.signal()

    with assert_raises(InterruptException):
        t1.result

    t1.wait()
    assert t1.is_interrupted

    t2.wait()
    assert not t2.is_interrupted
    try:
        Task.wait_all([t1, t2])
    except AggregateException as ex:
        ex.handle(lambda e: isinstance(e, InterruptException))

    t3 = Task.run(fn_raise_unrelated_signal)
    t3.wait()
    assert t3.is_failed

    signal1 = Event()
    signal3 = InterruptSignal()
    t3 = Task.create(interrupt=signal3.interrupt).run(fn_wait_for_signal, signal3.interrupt, signal1)
    signal1.wait()
    signal3.signal()
    t3.wait()
    assert t3.is_interrupted


def test_continuations(internals):
    # assertions on task start and finish time, based on time.sleep is risky,
    # since starting time isn't guaranteed on sceduler and internal events
    # might not react as fast as the test requires

    with ConcurrentTaskScheduler(8) as scheduler:
        test_str = "test"
        t1 = Task.plan(fn_return_value_after_time, 0.005, test_str)
        t2 = t1.continue_with(ContinuationOptions.DEFAULT, fn_continue_and_return_result_or_state)
        t3 = t2.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.ON_INTERRUPTED, fn_continue_and_return_result_or_state)
        _ = t3.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE, fn_continue_and_return_result_or_state)
        t4 = t1.continue_with(ContinuationOptions.DEFAULT, fn_continue_and_return_result_or_state_with_mods, 45, y=2)
        t1.schedule(scheduler)

        cs5 = InterruptSignal()
        t5 = Task.create(interrupt=cs5.interrupt).plan(fn_return_value_after_time, 0.05, test_str)
        t6 = t5.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY, fn_continue_and_return_result_or_state)
        t7 = t5.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.ON_INTERRUPTED, fn_continue_and_return_result_or_state)
        t5.schedule(scheduler)
        sleep(0.001)
        cs5.signal()
        sleep(.05)
        t7.wait()

        assert t4.result.endswith(" "+str(45*2))
        with assert_raises(InterruptException):
            t6.result # t6 is implicitly interrupted and will throw an exception

        t8 = Task.plan(fn_return_value_after_time, 0.01, "Task 8 done")
        t9 = Task[str].plan(fn_return_value_after_time, 0.001, "Task 9 done")
        t10 = Task.with_any([t8, t9]).run(fn_get_first_result_from_tasks)
        t11 = Task.with_all([t8, t9]).run(fn_get_first_result_from_tasks)
        t12 = Task.with_all([t8, t9]).run(fn_get_count_of_tasks)
        t8.schedule(scheduler)
        t9.schedule(scheduler)
        Task.wait_all([t10, t11])


        assert t10.result in ("Task 8 done", "Task 9 done")
        assert t11.result == "Task 8 done"
        assert t12.result == 2

        Task.wait_all([t10, t11])
        Task.wait_all([
            Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.01, "Task 121 done"),
            Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.03, "Task 122 done"),
            Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.02, "Task 123 done"),
            Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.001, "Task 124 done"),
        ])

        t12 = Task.create(scheduler=scheduler).run(fn_fail_immediately, "Error")
        assert t12.continue_with(ContinuationOptions.ON_FAILED, fn_continue_and_return_result_or_state).result == TaskState.FAILED.name

        with assert_raises(AggregateException):
            Task.wait_any([
                Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.1, "Task 121 done"),
                Task.create(scheduler=scheduler).run(fn_fail_immediately, "Error"),
            ])

        with assert_raises(AggregateException):
            Task.wait_all([
                Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.01, "Task 121 done"),
                Task.create(scheduler=scheduler).run(fn_fail_immediately, "Error"),
            ])

        signal = InterruptSignal()

        with assert_raises(TaskException, match=escape(str(AwaitedTaskInterruptedError))):
            Task.wait_all([
                Task.create(scheduler=scheduler, interrupt=signal.interrupt).run(fn_return_value_after_time, 0.01, "Task 121 done"),
                Task.create(scheduler=scheduler, interrupt=signal.interrupt).run(fn_raise_interrupt, signal),
            ], fail_on_interrupt=True)

        signal = InterruptSignal()

        with assert_raises(TaskException, match=escape(str(AwaitedTaskInterruptedError))):
            Task.wait_any([
                Task.create(scheduler=scheduler, interrupt=signal.interrupt).run(fn_return_value_after_time, 0.01, "Task 121 done"),
                Task.create(scheduler=scheduler, interrupt=signal.interrupt).run(fn_raise_interrupt, signal),
            ], fail_on_interrupt=True)

        signal = InterruptSignal()

        t13 = Task.with_any([
            Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.1, "Task 121 done"),
        ], interrupt=signal.interrupt).run(fn_get_count_of_tasks)
        signal.signal()
        t13.wait()

        assert Task.wait_any([
            Task.create(scheduler=scheduler).run(fn_return_value_after_time, 0.01, "Task 121 done"),
        ])


def test_lazy_task(internals):
    test_str = "test"
    t1 = Task.create(lazy=True).plan(fn_return_value_after_time, 0.005, test_str)
    t2 = Task.create(lazy=True).plan(fn_return_value_after_time, 0.005, test_str)
    t3 = Task.create(lazy=True).plan(fn_return_value_after_time, 0.005, test_str)
    assert not t1.is_scheduled
    assert not t1.is_completed
    assert t1.is_lazy

    result = t1.result # will be scheduled and run in the default scheduler
    assert t1.is_completed
    assert result == test_str

    result = Task.run(fn_continue_and_return_result_or_state, t2).result
    assert t2.is_completed
    assert result == test_str

    t3.wait()
    assert t2.is_completed
    assert result == test_str


def test_run_after(internals):
    t1 = Task.run_after(0.01, fn_return_value_after_time, 0, "test")
    assert t1.result == "test"

    with ConcurrentTaskScheduler(2) as scheduler:
        t1 = Task.create(scheduler=scheduler).run_after(0.01, fn_return_value_after_time, 0, "test")
        assert t1.result == "test"

