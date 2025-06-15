# pyright: basic
from typing import Iterable, Any, List
from time import sleep
from random import randint
from pytest import raises as assert_raises, fixture

from runtime.threading import InterruptSignal, Interrupt, ThreadingException
from runtime.threading.tasks import AggregateException, InterruptException
from runtime.threading.parallel import distribute
from runtime.threading.parallel.pipeline import ProducerConsumerQueue

def test_basics():
    queue = ProducerConsumerQueue[str]()
    dist = distribute(queue.get_iterator())
    outputs: List[Iterable[str]] = []
    facit: List[str] = []
    for _ in range(5):
        outputs.append(dist.take())

    dist.start(Interrupt.none())

    with assert_raises(ThreadingException):
        dist.start(Interrupt.none())

    for _ in range(10):
        s = str(randint(1, 100000))
        facit.append(s)
        queue.put(s)

    queue.complete()
    facit = sorted(facit)

    for output in outputs:
        assert facit == sorted(output)

def test_cancellation():
    signal = InterruptSignal()
    queue = ProducerConsumerQueue[str]()
    dist = distribute(queue.get_iterator())
    outputs: List[Iterable[str]] = []
    facit: List[str] = []
    for _ in range(5):
        outputs.append(dist.take())

    dist.start(signal.interrupt)

    for _ in range(10):
        s = str(randint(1, 100000))
        facit.append(s)
        queue.put(s)

    signal.signal()

    for _ in range(10):
        s = str(randint(1, 100000))
        facit.append(s)
        queue.put(s)

    queue.complete()
    facit = sorted(facit)

    for output in outputs:
        with assert_raises(InterruptException):
            result = sorted(output)
