# pyright: basic
from typing import Iterable, Any, List
from time import sleep
from random import randint
from pytest import raises as assert_raises, fixture

from runtime.threading import InterruptSignal, Interrupt, ThreadingException, InterruptException
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler
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



# def test_stress_test():

#     n = 100
#     o = 1000
#     p = 5
#     items = [ i for i in range(o)]

#     with ConcurrentTaskScheduler(p+2) as scheduler:
#         for i in range(n):
#             print(f"test_example_6xxx {i=}/{n}")

#             distributor = distribute(items, scheduler = scheduler)

#             consumers = [
#                 distributor.take()
#                 for _ in range(p)
#             ]

#             task = distributor.start()

#             comsumed = [
#                 list(consumer)
#                 for consumer in consumers
#             ]

#             for result in comsumed:
#                 assert sum(result) == sum(items)
