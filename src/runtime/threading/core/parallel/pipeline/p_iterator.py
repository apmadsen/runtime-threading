from typing import TypeVar, Iterator, Protocol, runtime_checkable

from runtime.threading.core.interrupt import Interrupt

T = TypeVar("T", covariant=True)

@runtime_checkable
class PIterator(Iterator[T], Protocol):
    """The PIterator class is a protocol for parallel iterators which allows for
    interruptable iterations with timeouts.
    """

    def next(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> T:
        """Gets the next item.

        Args:
            timeout (float | None, optional): The no. of seconds to wait before raising a StopIteration exception. Defaults to None.
            interrupt (Interrupt | None, optional): An external interrupt used to cancel operation.. Defaults to None.
        """
        ... # pragma: no cover

    def __next__(self) -> T:
        return self.next()

