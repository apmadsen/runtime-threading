from typing import overload

from runtime.threading.core.interrupt import Interrupt

class InterruptSignal:
    """The InterruptSignal class is used to cancel tasks asynchronously by signaling an underlying Interrupt instance."""

    __slots__ = ["__interrupt", "__interrupt_fn"]

    @overload
    def __init__(self) -> None:
        """Creates a new InterruptSignal.
        """
        ...
    @overload
    def __init__(self, *linked_interrupts: Interrupt) -> None:
        """Creates a new InterruptSignal linked to other interrupts.

        Args:
            linked_interrupts (Sequence[Interrupt]: Linked interrupts.
        """
    def __init__(self, *linked_interrupts: Interrupt):
        self.__interrupt, self.__interrupt_fn = Interrupt._create(*linked_interrupts) # pyright: ignore[reportPrivateUsage]

    @property
    def is_signaled(self) -> bool:
        """Indicates if Interrupt has been signaled
        """
        return self.__interrupt.is_signaled

    @property
    def interrupt(self) -> Interrupt:
        """The associated Interrupt
        """
        return self.__interrupt

    def signal(self) -> None:
        """Requests cancellation.
        """
        self.__interrupt_fn()
