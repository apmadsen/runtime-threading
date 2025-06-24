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


def test_basics(internals):
    with PContext(4) as ctx:
        def fn(task: Task[float], item: int) -> Iterable[float]:
            assert ctx.interrupt.propagates_to(task.interrupt)
            yield item * 1.5

        f1 = PFn(fn)
        f2 = PFn(fn) | PFn(fn)

        items = [ i for i in range(10) ]
        result1 = f1(items)
        result2 = f2(items)

        facit1 = [ i * 1.5 for i in items ]
        facit2 = [ i * 1.5 * 1.5 for i in items ]

        assert sorted(result1) == facit1
        assert sorted(result2) == facit2

def test_error_handling(internals):
    def fn1(task: Task[float], item: int) -> Iterable[float]:
        yield item * 1.5

    def fn2(task: Task[float], item: float) -> Iterable[float]:
        yield item * 2.0

    # test single PFn
    fn = PFn(fn1)
    fn([1,2,3,4,5]).drain()

    with assert_raises(AggregateException):
        fn([1,2,3,"a",4,5]).drain() # pyright: ignore[reportArgumentType]

    # test chained PFn's
    fn = PFn(fn1) | PFn(fn2)
    fn([1,2,3,4,5]).drain()

    with assert_raises(AggregateException):
        fn([1,2,3,"a",4,5]).drain() # pyright: ignore[reportArgumentType]


    # test PFork
    pl = PFn(fn1) | [
        PFn(fn2)
    ]

    with assert_raises(AggregateException):
        pl([1,2,3,"a",4,5]).drain() # pyright: ignore[reportArgumentType]



