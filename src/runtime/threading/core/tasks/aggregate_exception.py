from typing import Iterable, Callable, Sequence

from runtime.threading.core.threading_exception import ThreadingException

class AggregateException(ThreadingException):
    """The AggregateException exception is raised from operations awaiting results of several tasks.
    It may contain one or several exceptions raised from one or several tasks.
    """

    __slots__ = ["__exceptions"]

    def __init__(self, exceptions: Sequence[Exception]):
        super().__init__("One or more tasks failed")
        self.__exceptions = exceptions

    @property
    def exceptions(self) -> Iterable[Exception]:
        """The caught exceptions
        """
        return self.__exceptions

    def handle(self, predicate: Callable[[Exception], bool]):
        """Handles the aggregated exceptions. Any unhandled exceptions will result in a new AggregateException raised.

        Arguments:
            predicate (Callable[[Exception], bool]): The exception handler

        Raises:
            AggregateException: The remaining unhandled exceptions
        """
        unhandled: Sequence[Exception] = []
        for exception in self.__exceptions:
            if not predicate(exception):
                unhandled.append(exception)

        if len(unhandled) > 0:
            raise AggregateException(unhandled)

    def flatten(self) -> Exception:
        """If only one exception was thrown, this exception is returned, otherwise the AggregateException instance itself is returned.
        """
        if len(self.__exceptions) > 1:
            return self

        exception: Exception = self.__exceptions[0]

        while isinstance(exception, AggregateException):
            flattened = exception.flatten()
            if flattened is exception:
                break
            exception = flattened

        return exception
