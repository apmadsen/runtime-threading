# pyright: basic
from pytest import raises as assert_raises, fixture

def test_example_1():

    from runtime.threading.parallel import ProducerConsumerQueue
    from runtime.threading.tasks import Task

    def fn_produce(task: Task[None], queue: ProducerConsumerQueue[int], n: int) -> None:
        try:
            for i in range(n):
                queue.put(i)
            queue.complete()
        except Exception as ex:
            queue.fail(ex)

    def fn_consume(task: Task[list[int]], queue: ProducerConsumerQueue[int]) -> list[int]:
        return [ i for i in queue.get_iterator() ]

    queue = ProducerConsumerQueue[int]()
    task_producer = Task.run(fn_produce, queue, 5)
    task_consumer = Task.run(fn_consume, queue)

    assert task_consumer.result == list(range(5))
    assert task_producer.is_completed_successfully

def test_example_2():

    from typing import Iterable
    from random import randint
    from runtime.threading.tasks import Task
    from runtime.threading import parallel

    def fn_process(task: Task[Iterable[float]], item: int) -> Iterable[float]:
        yield 2 * item

    items = [ randint(0, 100000) for _ in range(1000) ]
    facit = sorted(list(map(lambda x: 2 * x, items)))

    output = parallel.process(items, parallelism = 5).do(fn_process)
    result = sorted([ item for item in output ])

    assert len(result) == len(items)
    assert facit == result

def test_example_3():
    from typing import Iterable
    from random import randint
    from runtime.threading.tasks import Task
    from runtime.threading import parallel

    def fn(task: Task[Iterable[int]], s: int) -> Iterable[int]:
        yield s * 2

    items = [ randint(0,100000) for _ in range(100)]
    t1 = parallel.map(items, parallelism=5).do(fn)

    result = sum(item for item in t1)

    facit = sum(map(lambda x: x*2, items))
    assert facit == result

def test_example_4():
    from random import randint
    from runtime.threading.tasks import Task, ContinuationOptions
    from runtime.threading import parallel

    queue = parallel.ProducerConsumerQueue[int]()

    def fn(task: Task[None], s: int) -> None:
        queue.put(s * 2)

    def fn_done(task: Task[None], preceding_task: Task[None]) -> None:
        queue.complete()

    items = [ randint(0,100000) for _ in range(100)]
    task1 = parallel.for_each(items, parallelism=5).do(fn)
    task1.continue_with(ContinuationOptions.DEFAULT, fn_done)

    result = sum(item for item in queue.get_iterator())

    facit = sum(map(lambda x: x*2, items))
    assert facit == result

def test_example_5():
    from random import randint
    from runtime.threading.tasks import Task
    from runtime.threading import parallel

    queue = parallel.ProducerConsumerQueue[int]()
    items = [ randint(0,100000) for _ in range(100)]
    facit = sum(map(lambda x: x*2, items))

    def fn(task: Task[None], items: list[int]) -> None:
        for item in items:
            queue.put(item * 2)
        queue.complete()

    parallel.background(parallelism=5).do(fn, items)

    result = sum(item for item in queue.get_iterator())

    assert facit == result


def test_example_6():
    from random import randint
    from runtime.threading import parallel

    items = [ randint(0,100000) for _ in range(100)]

    distributor = parallel.distribute(items)

    consumers = [
        distributor.take()
        for _ in range(5)
    ]

    task = distributor.start()

    comsumed = [
        list(consumer)
        for consumer in consumers
    ]

    for result in comsumed:
        assert result == items
