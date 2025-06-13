# pyright: basic
from typing import Iterable, Any, List
from time import sleep
from random import randint
from pytest import raises as assert_raises, fixture

from runtime.threading.tasks import Task, InterruptSignal, Interrupt, AggregateException, TaskInterruptException
from runtime.threading import parallel
from runtime.threading.parallel import distribute, ProducerConsumerQueue

def test_do():
    def fn(task: Task[Any], s: float):
        task.interrupt.raise_if_signaled()
        sleep(s)

    t1 = parallel.background(parallelism=5).do(fn, 0.01)
    t1.wait()

    with parallel.ParallelContext(4):
        t2 = parallel.background().do(fn, 0.01)
        t2.wait()

def test_process():
    def fn_process(task: Task[float], item: int) -> Iterable[float]:
        return [2 * item]

    # test with a normal list iterable
    items = [ randint(0, 100000) for _ in range(1000) ]
    facit = sorted(list(map(lambda x: 2 * x, items)))

    output = parallel.process(items, parallelism = 5, interrupt = Interrupt.none()).do(fn_process)
    result = sorted([ item for item in output ])

    assert len(result) == len(items)
    assert facit == result

    # test with a ProducerConsumerQueue iterable
    pcq_items = ProducerConsumerQueue[int](items)
    output = parallel.process(pcq_items.get_iterator(), parallelism = 5, interrupt = Interrupt.none()).do(fn_process)
    result = sorted([ item for item in output ])

    assert len(result) == len(items)
    assert facit == result

    with parallel.ParallelContext(4):
        output = parallel.process(items).do(fn_process)
        result = sorted([ item for item in output ])

        assert len(result) == len(items)
        assert facit, result


def test_process_error():
    items = [ randint(0, 100000) for _ in range(1000) ]

    def fn_process(task: Task[float], item: int) -> Iterable[float]:
        raise Exception()

    output = parallel.process(items, parallelism = 5, interrupt = Interrupt.none()).do(fn_process)

    with assert_raises(AggregateException):
        getattr(output, "__next__")()


def test_process_cancel():
    items = [ randint(0, 100000) for _ in range(1000) ]
    cs = InterruptSignal()

    def fn_process(task: Task[float], item: int) -> Iterable[float]:
        task.interrupt.raise_if_signaled()
        cs.signal()
        sleep(0.01)
        yield item * 1.5


    output = parallel.process(items, parallelism = 5, interrupt=cs.interrupt).do(fn_process)
    with assert_raises(TaskInterruptException):
        getattr(output, "__next__")()


def test_for_each():
    queue = ProducerConsumerQueue[int]()
    def fn(task: Task[Any], s: int) -> None:
        queue.put(s)

    items = [ randint(0,100000) for _ in range(100)]
    t1 = parallel.for_each(items, parallelism=5).do(fn)
    t1.wait()
    queue.complete()

    count = 0
    vsum = 0
    for item in queue.get_iterator():
        count +=1
        vsum += item

    facit = sum(map(lambda x: x, items))
    assert facit == vsum
    assert len(items) == count

    with parallel.ParallelContext(4):
        queue = ProducerConsumerQueue[int]()
        t2 = parallel.for_each(items).do(fn)
        t2.wait()
        queue.complete()

        count = 0
        vsum = 0
        for item in queue.get_iterator():
            count +=1
            vsum += item

        facit = sum(map(lambda x: x, items))
        assert facit == vsum
        assert len(items) == count

def test_map():
    def fn(task: Task[int], s: int) -> Iterable[int]:
        yield s*2

    items = [ randint(0,100000) for _ in range(100)]
    t1 = parallel.map(items, parallelism=5).do(fn)

    count = 0
    vsum = 0
    for item in t1:
        count +=1
        vsum += item

    facit = sum(map(lambda x: x*2, items))
    assert facit == vsum
    assert len(items) == count

    with parallel.ParallelContext(4):
        t2 = parallel.map(items).do(fn)

        count = 0
        vsum = 0
        for item in t2:
            count +=1
            vsum += item

        facit = sum(map(lambda x: x*2, items))
        assert facit == vsum
        assert len(items) == count

def test_distribute():
    queue = ProducerConsumerQueue[str]()
    dist = distribute(queue.get_iterator())
    outputs: List[Iterable[str]] = []
    facit: List[str] = []
    for _ in range(5):
        outputs.append(dist.take())

    dist.start(Interrupt.none())

    for _ in range(10):
        s = str(randint(1, 100000))
        facit.append(s)
        queue.put(s)

    queue.complete()
    facit = sorted(facit)

    for output in outputs:
        assert facit == sorted(output)


