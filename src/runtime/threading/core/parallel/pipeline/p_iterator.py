from typing import TypeVar, Iterator, Protocol, runtime_checkable

from runtime.threading.core.interrupt import Interrupt

T = TypeVar("T", covariant=True)

@runtime_checkable
class PIterator(Iterator[T], Protocol):

    def next(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> T:
        ...

    def __next__(self) -> T:
        return self.next()

