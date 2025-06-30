from typing import overload

from runtime.threading.core.interrupt import Interrupt

class InterruptSignal:
    """The InterruptSignal class is used to interrupt tasks asynchronously
    by signaling an underlying Interrupt instance.
    """

    __slots__ = ["__interrupt", "__interrupt_fn"]

    @overload
    def __init__(self) -> None:
        """Creates a new InterruptSignal.
        """
        ...
    @overload
    def __init__(self, *linked_interrupts: Interrupt) -> None:
        """Creates a new InterruptSignal linked to one or more other interrupts.

        Args:
            linked_interrupts (*Interrupt: Linked interrupts.
        """
    def __init__(self, *linked_interrupts: Interrupt):
        self.__interrupt, self.__interrupt_fn = Interrupt._create(*linked_interrupts) # pyright: ignore[reportPrivateUsage]


    @property
    def interrupt(self) -> Interrupt:
        """The associated Interrupt which will be signaled
        by calling signal() on this instance.
        """
        return self.__interrupt

    def signal(self) -> None:
        """Signals associated Interrupt.
        """
        self.__interrupt_fn(id(self))
