from runtime.threading.core.interrupt import Interrupt

from runtime.threading.core.threading_exception import ThreadingException

class InterruptException(ThreadingException):
    __slots__ = ["__interrupt"]

    def __init__(self, interrupt: Interrupt):
        super().__init__("Task or process was canceled")
        self.__interrupt = interrupt

    @property
    def interrupt(self) -> Interrupt:
        """The Interrupt associated with the exception
        """
        return self.__interrupt