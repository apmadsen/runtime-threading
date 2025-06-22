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
    with PContext(2, scheduler=ConcurrentTaskScheduler(8)) as ctx3:
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

    # with assert_raises(AggregateException):
    #     pl([1,2,3,"a",4,5]).drain() # pyright: ignore[reportArgumentType]
    with assert_raises(TypeError, match="can't multiply sequence by non-int of type 'float'"):
        pl([1,2,3,"a",4,5]).drain() # pyright: ignore[reportArgumentType]



def test_pfilter(internals):
    queue1 = ProducerConsumerQueue[int]([ i for i in range(1000) ])

    def filter(item: int) -> bool:
        return item % 2 == 0
    def fn(task: Task[int], item: int) -> Iterable[int]:
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



def test_pfork(internals):
    items = [ i for i in range(1000) ]
    signal = InterruptSignal()

    def fn(task: Task[int], item: int) -> Iterable[int]:
        task.interrupt.raise_if_signaled()
        yield item * 2


    with PContext(4, interrupt=signal.interrupt) as ctx:
        # call without a parent - not the intended way to use PFork
        f1 = PFork[int, int](( PFn(fn), ))
        signal.signal()

        with assert_raises(InterruptException):
            result = list(f1(items))


    # call without a parent - not the intended way to use PFork
    f1 = PFork[int, int](( PFn(fn), ))

    facit = [ i * 2 for i in items ]
    result = f1(items)

    assert sorted(result) == facit

    # baseline_pfork((2,), 10)

