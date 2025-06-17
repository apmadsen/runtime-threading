# pyright: basic
from typing import Iterable, List
from datetime import datetime
from pytest import raises as assert_raises, fixture

from runtime.threading import InterruptSignal, Interrupt
from runtime.threading.tasks import Task, AggregateException
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn, PContext, ProducerConsumerQueue
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

from tests.parallel.pipeline.baseline_pfn import baseline_pfn
from tests.parallel.pipeline.baseline_pfork import baseline_pfork

def test_pfn():
    baseline_pfn((2,), 10)

def test_error_handling():
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

    with assert_raises(TypeError, match="can't multiply sequence by non-int of type 'float'"):
        pl([1,2,3,"a",4,5]).drain() # pyright: ignore[reportArgumentType]



def test_pfilter():
    queue = ProducerConsumerQueue[int]([ i for i in range(1000) ])

    def filter(item: int) -> bool:
        return item % 2 == 0
    def fn(task: Task[int], item: int) -> Iterable[int]:
        yield item * 2

    with ConcurrentTaskScheduler(4) as scheduler:
        with PContext(4, scheduler = scheduler):
            f1 = NullPFn() | filter | PFn(fn)

            facit = [ o * 2 for o in range(1000) if o % 2 == 0 ]
            results = [ o for o in f1(queue.get_iterator()) ]

    assert sorted(results) == facit


def test_pfork():
    baseline_pfork((2,), 10)

