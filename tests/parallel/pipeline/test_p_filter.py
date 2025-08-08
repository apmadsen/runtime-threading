# pyright: basic
# ruff: noqa
from typing import Iterable, Any
from datetime import datetime
from pytest import raises as assert_raises, fixture
from re import escape

from runtime.threading import InterruptSignal, Interrupt, InterruptException
from runtime.threading.tasks import Task, AggregateException, TaskException
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn, PContext, PFork
from runtime.threading.parallel import ProducerConsumerQueue
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler, TaskScheduler

from tests.parallel.pipeline.baseline_pfn import baseline_pfn
from tests.parallel.pipeline.baseline_pfork import baseline_pfork



def test_pfilter(internals):
    queue1 = ProducerConsumerQueue[int]([ i for i in range(1000) ])

    def filter(task: Task[Iterable[int]], item: int) -> bool:
        return item % 2 == 0
    def fn(task: Task[Iterable[int]], item: int) -> Iterable[int]:
        yield item * 2

    # implicit function to filter
    with ConcurrentTaskScheduler(4) as scheduler:
        with PContext(4, scheduler = scheduler):
            f1 = NullPFn() | filter | PFn(fn)

            facit = [ o * 2 for o in range(1000) if o % 2 == 0 ]
            results = [ o for o in f1(queue1.get_iterator()) ]

    assert sorted(results) == facit

    queue2 = ProducerConsumerQueue[int]([ i for i in range(1000) ])

    # catch all filter
    with ConcurrentTaskScheduler(4) as scheduler:
        with PContext(4, scheduler = scheduler):
            f2 = NullPFn() | PFilter()

            facit = [ o for o in range(1000) ]
            results = [ o for o in f2(queue2.get_iterator()) ]

    assert sorted(results) == facit

