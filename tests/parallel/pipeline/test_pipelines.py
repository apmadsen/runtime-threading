# pyright: basic
# ruff: noqa
from typing import Iterable
from pytest import raises as assert_raises, fixture


from runtime.threading import InterruptSignal, Interrupt, InterruptException
from runtime.threading.tasks import Task, AggregateException, TaskException
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn, PContext, PFork
from runtime.threading.parallel import ProducerConsumerQueue
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler, TaskScheduler

from tests.parallel.pipeline.baseline_pfn import baseline_pfn
from tests.parallel.pipeline.baseline_pfork import baseline_pfork


def test_basics(internals):
    with PContext(4) as ctx:
        def fn(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
            assert ctx.interrupt.propagates_to(task.interrupt)
            task.interrupt.raise_if_signaled()
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
    with ConcurrentTaskScheduler(8) as scheduler:
        with PContext(4, scheduler=scheduler):

            def fn1(task: Task[Iterable[float]], item: int) -> Iterable[float]:
                task.interrupt.raise_if_signaled()
                yield item * 1.5

            def fn2(task: Task[Iterable[float]], item: float) -> Iterable[float]:
                task.interrupt.raise_if_signaled()
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

    assert scheduler.allocated_threads == scheduler.suspended_threads == 0


def test_example1(internals):
    from runtime.threading.tasks import Task
    from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler
    from runtime.threading.parallel.pipeline import PFn, PFilter, PContext

    with ConcurrentTaskScheduler(4) as scheduler:
        with PContext(scheduler.max_parallelism, scheduler = scheduler) as ctx:

            def fn_filter_uneven(task: Task[Iterable[int|float]], item: int|float) -> bool:
                return item % 2 == 0

            def fn_multiply(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
                task.interrupt.raise_if_signaled()
                yield item * 1.5

            def fn_divide(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
                task.interrupt.raise_if_signaled()
                yield item / 2

            pipeline = (
                PFilter(fn_filter_uneven) # filters out all uneven numbers bringing the workload down from 1000 to 500 items
                  | PFn(fn_multiply) # multiplies by 1.5
                  | [
                      PFn(fn_divide), # divides by 2
                      PFn(fn_divide) # divides by 2
                    ] # the fork multiplies the workload with the no. of functions in it bringing the workload up from 500 to 1000
            )

            o = 1000
            facit = [ ((i * 1.5) / 2) for i in range(o) if i % 2 == 0]
            result = list(pipeline(range(o))) # -> 1000 items

            assert set(facit) == set(result)

            x=0