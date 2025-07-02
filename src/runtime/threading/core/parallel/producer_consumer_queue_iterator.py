from __future__ import annotations
from typing import TypeVar, TYPE_CHECKING

from runtime.threading.core.parallel.pipeline.p_iterable import PIterable, PIterator
from runtime.threading.core.interrupt import Interrupt

if TYPE_CHECKING:
    from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue

T = TypeVar('T')

class ProducerConsumerQueueIterator(PIterable[T], PIterator[T]):
    """The ProducerConsumerQueueIterator class is a parallel Iterator/Iterable class
    which allows for interruption of the iteration.
    """
    __slots__ = ["__queue"]

    def __init__(self, queue: ProducerConsumerQueue[T]):
        self.__queue = queue

    def __iter__(self) -> PIterator[T]:
        return self

    def next(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> T:
        try:
            return self.__queue.take(timeout, interrupt)
        except TimeoutError:
            raise StopIteration
