from typing import TypeVar, Iterator, Protocol, runtime_checkable

from runtime.threading.core.interrupt import Interrupt

T = TypeVar("T", covariant=True)

@runtime_checkable
class PIterator(Iterator[T], Protocol):
    """The PIterator class is a protocol for parallel iterators which allows for
    interruptable iterations with timeouts.
    """

    def next(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> T:
        ... # pragma: no cover

    def __next__(self) -> T:
        return self.next()

