# pyright: basic
from typing import Iterable, List
from datetime import datetime
from pytest import raises as assert_raises, fixture

from runtime.threading import InterruptSignal, Interrupt
from runtime.threading.tasks import Task, AggregateException
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn, PContext
from runtime.threading.parallel import ProducerConsumerQueue
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

def baseline_pfork(parallelism: tuple[int, ...], count: int):
    s = 0.0001
    c = 3

    facit1 = [ i+1 for i in range(count) ]
    facit2 = [ i+1000+500 for i in facit1 if i % 2 == 0 ]
    facit2 += [ i+2000 for i in facit1 if i % 2 != 0 and i % 3 == 0 ]
    facit2 += [ i+3000 for i in facit1 if i % 2 != 0 and i % 3 != 0 ]
    facit = [ f + 10000 for f in facit2 ]
    facit = sorted(facit)


    def fn0(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
        yield item + 1
    def fn1(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
        yield item + 1000
    def fn1_1(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
        yield item + 500
    def fn2(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
        yield item + 2000
    def fn3(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
        yield item + 3000
    def fn4(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
        yield item + 10000


    for p in parallelism:
        pl = PFn(fn0, p) | [
            PFilter[int|float](lambda t, o: o % 2 == 0) | PFn(fn1, p) | PFn(fn1_1, p),
            PFilter[int|float](lambda t, o: o % 2 != 0 and o % 3 == 0) | PFn(fn2, p),
            PFilter[int|float](lambda t, o: o % 2 != 0 and o % 3 != 0) | PFn(fn3, p)
        ] | PFn(fn4, p)

        with ConcurrentTaskScheduler(p) as scheduler:
            with PContext(p, scheduler=scheduler):
                ts = datetime.now()
                result: List[float] = []
                for _ in range(c):
                    queue = ProducerConsumerQueue[int]([ i for i in range(count) ])
                    result = [ r for r in pl(queue.get_iterator()) ]
                    assert facit == sorted(result)

                print(f"Parallelism={p} : {(datetime.now()-ts).total_seconds() / c:.3f} / {(6*count*s)/p:.5f}")
                assert facit == sorted(result)

    _=0


if __name__ == "__main__":
    baseline_pfork((2, 4, 8), 100)