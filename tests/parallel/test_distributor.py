# pyright: basic
from typing import Iterable, Any, List
from time import sleep
from random import randint
from pytest import raises as assert_raises, fixture

from runtime.threading import InterruptSignal, Interrupt, ThreadingException, InterruptException
from runtime.threading.tasks import AggregateException
from runtime.threading.parallel import distribute, ProducerConsumerQueue

def test_basics(internals):
    queue = ProducerConsumerQueue[str]()
    dist = distribute(queue.get_iterator())
    outputs: List[Iterable[str]] = []
    facit: List[str] = []
    for _ in range(5):
        outputs.append(dist.take())

    dist.start()

    with assert_raises(ThreadingException, match="Distribution has already begun"):
        dist.start()

    with assert_raises(ThreadingException, match="Distribution has already begun"):
        dist.take()

    for _ in range(10):
        s = str(randint(1, 100000))
        facit.append(s)
        queue.put(s)

    queue.complete()
    facit = sorted(facit)

    for output in outputs:
        assert facit == sorted(output)

def test_interruption(internals):
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

