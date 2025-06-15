# pyright: basic
from typing import Iterable, List
from datetime import datetime
from pytest import raises as assert_raises, fixture

from runtime.threading import InterruptSignal, Interrupt
from runtime.threading.tasks import Task, AggregateException
from runtime.threading.parallel.pipeline import PFn, PFilter, NullPFn, PContext, ProducerConsumerQueue
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

def baseline_pfn(parallelism: tuple[int, ...]):
    c = 1
    r = 100

    def fn1(task: Task[float], item: int) -> Iterable[float]:
        yield item * 1.5
    def fn2(task: Task[float], item: float) -> Iterable[float]:
        yield item * 2



    facit = [ i * 1.5 * 2 * 2 for i in range(r) ]

    from datetime import datetime
    for p in parallelism:
        with ConcurrentTaskScheduler(p) as scheduler:
            with PContext(p, Interrupt.none(), scheduler):
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

if __name__ == "__main__":
    baseline_pfn((2, 4, 8))