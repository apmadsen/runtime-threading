from typing import TypeVar, Iterator
from abc import ABC, abstractmethod

from runtime.threading.core.tasks.interrupt import Interrupt

T = TypeVar("T")

class PIterator(ABC, Iterator[T]):

    @abstractmethod
    def next(self, timeout: float | None = None, interrupt: Interrupt = Interrupt.none()) -> T:
        ...

    def __next__(self) -> T:
        return self.next()

