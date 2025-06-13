# pyright: basic
from typing import Iterable, List
from datetime import datetime
from pytest import raises as assert_raises, fixture

from runtime.threading.tasks import Task, Interrupt, AggregateException
from runtime.threading.parallel import ProducerConsumerQueue, ParallelContext
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

def test_pfn():
    ps = [2,4,8]
    c = 1
    r = 100

    def fn1(task: Task[float], item: int) -> Iterable[float]:
        yield item * 1.5
    def fn2(task: Task[float], item: float) -> Iterable[float]:
        yield item * 2



    facit = [ i * 1.5 * 2 * 2 for i in range(r) ]

    from datetime import datetime
    for p in ps:
        with ConcurrentTaskScheduler(p) as scheduler:
            with ParallelContext(p, Interrupt.none(), scheduler):
                ts = datetime.now()
                result: List[float] = []
                for _ in range(c):
                    q = ProducerConsumerQueue[int]([ i for i in range(r)])
                    # f = PFn(fn1, 0.33) | PFn(fn2, 0.33) | PFn(fn2, 0.33)
                    f = PFn(fn1, p) | PFn(fn2, p) | PFn(fn2, p)

                    it = f(q.get_iterator())
                    result = sorted([o for o in it ])

                print(f"Parallelism={p} : {(datetime.now()-ts).total_seconds() / c:.3f} / {r/p:.1f}")
                assert facit == result


def test_error_handling():
    def fn1(task: Task[float], item: int) -> Iterable[float]:
        yield item * 1.5


    def fn2(task: Task[float], item: float) -> Iterable[float]:
        yield item * 2.0

    # test single PFn
    fn = PFn(fn1)
    fn([1,2,3,4,5]).drain()

    with assert_raises(AggregateException):
        fn([1,2,3,"a",4,5]).drain() # type: ignore

    # test chained PFn's
    fn = PFn(fn1) | PFn(fn2)
    fn([1,2,3,4,5]).drain()

    with assert_raises(Exception):
        fn([1,2,3,"a",4,5]).drain() # type: ignore


    # test PFork
    pl = PFn(fn1) | [
        PFn(fn2)
    ]

    with assert_raises(Exception):
        pl([1,2,3,"a",4,5]).drain() # type: ignore

    _=0


def test_pfilter():
    queue = ProducerConsumerQueue[int]([ i for i in range(1000) ])

    def filter(item: int) -> bool:
        return item % 2 == 0
    def fn(task: Task[int], item: int) -> Iterable[int]:
        yield item * 2

    with ConcurrentTaskScheduler(4) as scheduler:
        with ParallelContext(4, Interrupt.none(), scheduler):
            f1 = NullPFn() | filter | PFn(fn)

            facit = [ o * 2 for o in range(1000) if o % 2 == 0 ]
            results = [ o for o in f1(queue.get_iterator()) ]

    assert sorted(results) == facit
    _=0

def test_pfork():
    r = 100
    s = 0.0001
    c = 3

    facit1 = [ i+1 for i in range(r) ]
    facit2 = [ i+1000+500 for i in facit1 if i % 2 == 0 ]
    facit2 += [ i+2000 for i in facit1 if i % 2 != 0 and i % 3 == 0 ]
    facit2 += [ i+3000 for i in facit1 if i % 2 != 0 and i % 3 != 0 ]
    facit = [ f + 10000 for f in facit2 ]
    facit = sorted(facit)


    def fn0(task: Task[int], item: int) -> Iterable[int]:
        yield item + 1
    def fn1(task: Task[float], item: int) -> Iterable[float]:
        yield item + 1000
    def fn1_1(task: Task[float], item: float) -> Iterable[float]:
        yield item + 500
    def fn2(task: Task[float], item: int) -> Iterable[float]:
        yield item + 2000
    def fn3(task: Task[float], item: int) -> Iterable[float]:
        yield item + 3000
    def fn4(task: Task[float], item: float) -> Iterable[float]:
        yield item + 10000


    for p in [2, 4, 8]:
        pl = PFn(fn0, p) | [
            PFilter[int](lambda o: o % 2 == 0) | PFn[int, float](fn1, p) | PFn(fn1_1, p),
            PFilter[int](lambda o: o % 2 != 0 and o % 3 == 0) | PFn(fn2, p),
            PFilter[int](lambda o: o % 2 != 0 and o % 3 != 0) | PFn(fn3, p)
        ] | PFn(fn4, p)

        with ConcurrentTaskScheduler(p) as scheduler:
            with ParallelContext(p, Interrupt.none(), scheduler):
                ts = datetime.now()
                result: List[float] = []
                for _ in range(c):
                    queue = ProducerConsumerQueue[int]([ i for i in range(r) ])
                    result = [ r for r in pl(queue.get_iterator()) ]
                    assert facit == sorted(result)

                print(f"Parallelism={p} : {(datetime.now()-ts).total_seconds() / c:.3f} / {(6*r*s)/p:.5f}")
                assert facit == sorted(result)

    _=0


