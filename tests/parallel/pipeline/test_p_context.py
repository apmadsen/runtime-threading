# pyright: basic
from typing import Iterable, Any
from datetime import datetime
from pytest import raises as assert_raises, fixture
from re import escape

from runtime.threading import InterruptSignal, Interrupt, InterruptException
from runtime.threading.tasks import Task, AggregateException, TaskCanceledError, TaskException
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn, PContext, PFork
from runtime.threading.parallel import ProducerConsumerQueue
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler, TaskScheduler

from tests.shared_functions import fn_return_value_after_time

def test_p_context(internals):
    default_scheduler = TaskScheduler.default()
    root = PContext.root()
    current = PContext.current()
    assert current is root

    with PContext(2) as ctx1:
        assert PContext.current() is ctx1
        assert PContext.current() is not root
        assert ctx1.scheduler is default_scheduler

        with PContext(2) as ctx2:
            assert ctx2 is not ctx1
            assert PContext.current() is ctx2
            assert PContext.current() is not root
            assert ctx2.scheduler is default_scheduler

    # check that tasks within PContext's attach to that PContext
    with ConcurrentTaskScheduler(8) as scheduler:
        with PContext(2, scheduler=scheduler) as ctx3:

            t1 = Task.run_after(0.01, fn_return_value_after_time, 0, "test")
            assert t1.result == "test"

            def fn(task: Task[Any]) -> bool:
                pc = PContext.current()
                assert pc is ctx3
                assert pc is not root
                assert TaskScheduler.current() is pc.scheduler
                return True

            assert ctx3.scheduler is not TaskScheduler.current()
            assert ctx3.scheduler is not default_scheduler

            subtask1 = Task.run(fn)
            assert subtask1.result

            subtask2 = Task.run(fn)
            assert subtask2.result

            subtask3 = Task.create(scheduler=default_scheduler).run(fn)
            with assert_raises(AssertionError):
                assert subtask3.result
            x=0
