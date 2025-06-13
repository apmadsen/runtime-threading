from typing import TypeVar, Iterable, overload
from abc import ABC, abstractmethod

from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.parallel.p_iterator import PIterator

T = TypeVar("T")

class PIterable(ABC, Iterable[T]):

    @abstractmethod
    def iter(self) -> PIterator[T]:
        ...

    @overload
    def drain(self) -> None:
        """Drains the PIterable from items.
        """
        ...
    @overload
    def drain(self, timeout: float | None = None, interrupt: Interrupt = Interrupt.none()) -> None:
        """Drains the PIterable from items.

        Args:
            timeout (float | None, optional): The operation timeout. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to Interrupt.none().
        """
        ...
    def drain(self, timeout: float | None = None, interrupt: Interrupt = Interrupt.none()) -> None:
        try:
            iterator = self.iter()
            while True:
                iterator.next(timeout, interrupt)
        except StopIteration:
            pass


    def __iter__(self) -> PIterator[T]:
        return self.iter()
