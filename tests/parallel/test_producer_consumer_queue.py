# pyright: basic
from typing import List, Any, Iterable, cast
from threading import Thread
from re import escape
from random import randint
from pytest import raises as assert_raises, fixture

from runtime.threading.parallel import ProducerConsumerQueue, ParallelException
from runtime.threading.core.parallel.producer_consumer_queue import QueueCompletedError, QueueLinkedToAnotherQueueError
from runtime.threading.tasks import Task
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler
from runtime.threading import InterruptSignal

def test_basics(internals):
    o = 100
    pcq = ProducerConsumerQueue[int]()
    t = Thread(target=add, args=(pcq, o))
    t.start()

    items: List[int] = []
    for item in pcq.get_iterator():
        items.append(item)

    assert o == len(items)

    items1 = [ randint(0, 100000) for _ in range(1000) ]
    pcq1 = ProducerConsumerQueue[int]()
    pcq2 = ProducerConsumerQueue[int](pcq1.get_iterator())

    assert not pcq1.is_async
    assert pcq2.is_async
    assert not pcq2.wait_event.wait(0)
    pcq1.put_many_async(items1).wait()
    pcq1.complete()

    with assert_raises(ParallelException, match=escape(str(QueueCompletedError))):
        pcq1.put(1)
    with assert_raises(ParallelException, match=escape(str(QueueLinkedToAnotherQueueError))):
        pcq2.put(1)
    with assert_raises(ParallelException, match=escape(str(QueueLinkedToAnotherQueueError))):
        pcq2.fail(Exception())
    with assert_raises(ParallelException, match=escape(str(QueueLinkedToAnotherQueueError))):
        pcq2.fail_if_not_complete(Exception())

    with assert_raises(ParallelException, match=escape(str(QueueCompletedError))):
        pcq1.put_many((1,2,3))
    with assert_raises(ParallelException, match=escape(str(QueueLinkedToAnotherQueueError))):
        pcq2.put_many((1,2,3))

    with assert_raises(ParallelException, match=escape(str(QueueCompletedError))):
        pcq1.complete()

    with assert_raises(ParallelException, match=escape(str(QueueLinkedToAnotherQueueError))):
        pcq2.complete()

    with assert_raises(ParallelException, match=escape(str(QueueLinkedToAnotherQueueError))):
        pcq2.fail_if_not_complete(Exception("Fail"))

    items = []
    for item in pcq2.get_iterator():
        items.append(item)


    assert items1 == items
    assert not pcq.is_failed

    pcq3 = ProducerConsumerQueue[int]()
    pcq3.fail_if_not_complete(Exception("Fail"))

    with assert_raises(Exception, match="Fail"):
        pcq3.try_take()

    assert pcq3.is_failed

def test_put_many(internals):
    test_items = [ randint(0, 100000) for _ in range(100) ]
    pcq = ProducerConsumerQueue[int]()
    t = Thread(target=add_many, args=(pcq, test_items))
    t.start()

    items: List[int] = []

    for item in pcq.get_iterator():
        items.append(item)


    assert test_items == items


def test_take(internals):
    o = 100
    pcq = ProducerConsumerQueue[int]([ i for i in range(o) ])

    items: List[int] = []
    sig = InterruptSignal()

    success = True
    while success:
        result, success = pcq.try_take(interrupt = sig.interrupt)
        if success:
            items.append(cast(int, result))


    assert o == len(items)

    pcq = ProducerConsumerQueue[int]()
    pcq.put_many([ i for i in range(o) ])

    items = []

    try:
        while True:
            result = pcq.take(0.01)
            items.append(cast(int, result))
    except TimeoutError:
        pass

    assert o == len(items)

def test_multiple_iterators(internals):
    o = 100
    p = 5
    pcq = ProducerConsumerQueue[int]([ i for i in range(o) ])

    def fn_consume(task: Task[list[int]], producer: ProducerConsumerQueue[int]) -> list[int]:
        result = []

        for item in pcq.get_iterator():
            result.append(item)
            task.interrupt.wait(0.01) # introduce some waiting to guarantee a fair distribution among the tasks

        return result

    with ConcurrentTaskScheduler(p) as scheduler:
        consumers = [
            Task.create(scheduler = scheduler).run(fn_consume, pcq)
            for _ in range(p)
        ]

        consumed = [
            list(consumer.result)
            for consumer in consumers
        ]

    for result in consumed:
        assert any(result)

    total = [ item for result in consumed for item in result ]
    assert len(total) == o


def test_chaining(internals):
    o = 100
    p = 5
    facit = [ i for i in range(o) ]
    pcq_initial = ProducerConsumerQueue[int](facit)
    pcq_prev = pcq_initial

    for _ in range(p):
        pcq_prev = ProducerConsumerQueue[int](pcq_prev.get_iterator())

    result = list(pcq_prev.get_iterator())
    assert sorted(result) == facit





def add(q: ProducerConsumerQueue[int], o: int):
    for i in range(o):
        q.put(i)
    q.complete()

def add_many(q: ProducerConsumerQueue[int], items: List[int]):
    q.put_many(items)
    q.complete()

