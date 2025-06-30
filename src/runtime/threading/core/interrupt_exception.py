from __future__ import annotations
from typing import TYPE_CHECKING

from runtime.threading.core.threading_exception import ThreadingException

if TYPE_CHECKING:
    from runtime.threading.core.interrupt import Interrupt

class InterruptException(ThreadingException):
    """The InterruptException exception is raised whenever raise_if_signaled()
    is called on a signaled Interrupt.
    """

    __slots__ = ["__interrupt"]

    def __init__(self, interrupt: Interrupt):
        super().__init__("Task or process was interrupted")
        self.__interrupt = interrupt

    @property
    def interrupt(self) -> Interrupt:
        """The Interrupt associated with the exception.
        """
        return self.__interrupt