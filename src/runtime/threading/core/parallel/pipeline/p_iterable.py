from typing import TypeVar, Iterable, Protocol, runtime_checkable, overload

from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.parallel.pipeline.p_iterator import PIterator

T = TypeVar("T", covariant=True)

@runtime_checkable
class PIterable(Iterable[T], Protocol):
    """The PIterable class is a protocol for parallel Iterables which allows for
    interruptable iterations with timeouts.
    """

    @overload
    def drain(self) -> None:
        """Drains the PIterable from items.
        """
        ...
    @overload
    def drain(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> None:
        """Drains the PIterable from items.

        Args:
            timeout (float | None, optional): The operation timeout. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.
        """
        ...
    def drain(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> None:
        try:
            iterator = self.__iter__()
            while True:
                iterator.next(timeout, interrupt)
        except StopIteration:
            pass


    def __iter__(self) -> PIterator[T]:
        ... # pragma: no cover
