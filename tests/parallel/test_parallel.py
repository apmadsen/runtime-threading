# pyright: basic
# ruff: noqa
from typing import Iterable, Any, cast
from pytest import raises as assert_raises, fixture

from runtime.threading.tasks import Task, AggregateException
from runtime.threading import parallel, ThreadingException, InterruptSignal, Interrupt, InterruptException, sleep
from runtime.threading.parallel import pipeline
from runtime.threading.concurrent import Queue

def test_background(internals):
    assert parallel.background() is parallel.background()

    items = tuple( i for i in range(100))
    input = Queue.from_items(items)
    output: Queue[int] = Queue()

    def fn(task: Task[Any], s: float):
        task.interrupt.raise_if_signaled()
        while result := input.try_dequeue():
            if not result[1]:
                break
            output.enqueue(cast(int, result[0]))


    parallel.background().do(fn, 0.01).wait()

    result = tuple(output)
    assert items == result

    input = Queue.from_items(items)
    output: Queue[int] = Queue()

    with pipeline.PContext(4) as ctx:
        parallel.background(scheduler=ctx.scheduler, interrupt=ctx.interrupt,parallelism=ctx.max_parallelism).do(fn, 0.01).wait()


    result = tuple(output)
    assert items == result


def test_process(internals):
    def fn_process(task: Task[Iterable[float]], item: int) -> Iterable[float]:
        return [2 * item]

    # test with a normal list iterable
    items = [ i for i in range(1000) ]
    facit = sorted(list(map(lambda x: 2 * x, items)))

    output = parallel.process(items, parallelism = 5).do(fn_process)
    result = sorted([ item for item in output ])

    assert len(result) == len(items)
    assert facit == result

    # test with a ProducerConsumerQueue iterable
    pcq_items = parallel.ProducerConsumerQueue[int](items)
    output = parallel.process(pcq_items.get_iterator(), parallelism = 5).do(fn_process)
    result = sorted([ item for item in output ])

    assert len(result) == len(items)
    assert facit == result

    with pipeline.PContext(4) as ctx:
        output = parallel.process(items, parallelism=ctx.max_parallelism,interrupt=ctx.interrupt).do(fn_process)
        result = sorted([ item for item in output ])

        assert len(result) == len(items)
        assert facit, result


def test_process_error(internals):
    items = [ i for i in range(1000) ]

    def fn_process(task: Task[Iterable[float]], item: int) -> Iterable[float]:
        raise Exception()

    output = parallel.process(items, parallelism = 5).do(fn_process)

    with assert_raises(AggregateException):
        getattr(output, "__next__")()


def test_process_interrupt(internals):
    items = [ i for i in range(1000) ]
    cs = InterruptSignal()

    def fn_process(task: Task[Iterable[float]], item: int) -> Iterable[float]:
        assert cs.interrupt.propagates_to(task.interrupt)
        task.interrupt.raise_if_signaled()
        cs.signal()
        yield item * 1.5


    output = parallel.process(items, parallelism = 3, interrupt=cs.interrupt).do(fn_process)

    with assert_raises(InterruptException):
        getattr(output, "__next__")()


def test_for_each(internals):
    queue = parallel.ProducerConsumerQueue[int]()
    def fn(task: Task[Any], s: int) -> None:
        queue.put(s)

    items = [ i for i in range(100)]
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

    with pipeline.PContext(4) as ctx:
        queue = parallel.ProducerConsumerQueue[int]()
        t2 = parallel.for_each(items, parallelism=ctx.max_parallelism,interrupt=ctx.interrupt).do(fn)
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

def test_map(internals):
    def fn(task: Task[Iterable[int]], s: int) -> Iterable[int]:
        yield s*2

    items = [ i for i in range(100)]
    t1 = parallel.map(items, parallelism=5).do(fn)

    count = 0
    vsum = 0
    for item in t1:
        count +=1
        vsum += item

    facit = sum(map(lambda x: x*2, items))
    assert facit == vsum
    assert len(items) == count

    with pipeline.PContext(4) as ctx:
        t2 = parallel.map(items, parallelism=ctx.max_parallelism,interrupt=ctx.interrupt).do(fn)

        count = 0
        vsum = 0
        for item in t2:
            count +=1
            vsum += item

        facit = sum(map(lambda x: x*2, items))
        assert facit == vsum
        assert len(items) == count
