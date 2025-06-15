# pyright: basic
from typing import List, cast
from time import sleep
from threading import Thread
from random import randint
from pytest import raises as assert_raises, fixture

from runtime.threading.parallel.pipeline import ProducerConsumerQueue


def test_basics():
    o = 100
    pcq = ProducerConsumerQueue[int]()
    t = Thread(target=add, args=(pcq, o))
    t.start()

    items: List[int] = []
    for item in pcq.get_iterator():
        items.append(item)

    assert o == len(items)

    items1 = [ randint(0, 100000) for _ in range(1000) ]
    pcq1 = ProducerConsumerQueue[int](items1)
    pcq2 = ProducerConsumerQueue[int](pcq1.get_iterator())

    items = []
    for item in pcq2.get_iterator():
        items.append(item)


    assert items1 == items


def test_put_many():
    test_items = [ randint(0, 100000) for _ in range(100) ]
    pcq = ProducerConsumerQueue[int]()
    t = Thread(target=add_many, args=(pcq, test_items))
    t.start()

    items: List[int] = []

    for item in pcq.get_iterator():
        items.append(item)


    assert test_items == items


def test_take():
    o = 100
    pcq = ProducerConsumerQueue[int]([ i for i in range(o) ])

    items: List[int] = []

    success = True
    while success:
        result, success = pcq.try_take()
        if success:
            items.append(cast(int, result))


    assert o == len(items)

    pcq = ProducerConsumerQueue[int]()
    pcq.put_many([ i for i in range(o) ])

    items = []

    try:
        while True:
            result, success = pcq.try_take(0.01)
            if success:
                items.append(cast(int, result))
    except TimeoutError:
        pass

    assert o == len(items)


def add(q: ProducerConsumerQueue[int], o: int):
    for i in range(o):
        q.put(i)
        sleep(0.0001)
    q.complete()

def add_many(q: ProducerConsumerQueue[int], items: List[int]):
    q.put_many(items)
    q.complete()

