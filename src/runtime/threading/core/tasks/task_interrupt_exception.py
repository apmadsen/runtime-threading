from runtime.threading.core.tasks.interrupt import Interrupt

from runtime.threading.core.tasks.threading_exception import ThreadingException

class TaskInterruptException(ThreadingException):
    __slots__ = ["__interrupt"]

    def __init__(self, interrupt: Interrupt):
        super().__init__("Task was canceled")
        self.__interrupt = interrupt

    @property
    def interrupt(self) -> Interrupt:
        """The Interrupt associated with the exception
        """
        return self.__interrupt