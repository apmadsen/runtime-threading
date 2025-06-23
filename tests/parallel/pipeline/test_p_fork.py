# pyright: basic
from typing import Iterable, Any
from datetime import datetime
from pytest import raises as assert_raises, fixture
from re import escape

from runtime.threading import InterruptSignal, Interrupt, InterruptException
from runtime.threading.tasks import Task, AggregateException, TaskCanceledError, TaskException
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn, PContext, PFork, ProducerConsumerQueue
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler, TaskScheduler

from tests.parallel.pipeline.baseline_pfn import baseline_pfn
from tests.parallel.pipeline.baseline_pfork import baseline_pfork


def test_pfork(internals):
    items = [ i for i in range(1000) ]

    # call without a parent - not the intended way to use PFork
    f1 = PFork[int, int](( PFn(fn, 2), ))

    facit = [ i * 2 for i in items ]
    result = f1(items)

    assert sorted(result) == facit

    # baseline_pfork((2,), 10)

def test_cancellation(internals):
    items = [ i for i in range(1000) ]
    signal = InterruptSignal()

    with PContext(4, interrupt=signal.interrupt) as ctx:
        # call without a parent - not the intended way to use PFork
        f1 = PFork[int, int](( PFn(fn, 2), ))
        signal.signal()

        with assert_raises(InterruptException):
            result = list(f1(items))


def fn(task: Task[int], item: int) -> Iterable[int]:
    task.interrupt.raise_if_signaled()
    yield item * 2