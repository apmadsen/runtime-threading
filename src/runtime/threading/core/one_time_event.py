from runtime.threading.core.event import Event
from runtime.threading.core.threading_exception import ThreadingException

class OneTimeEvent(Event):
    """The OneTimeEvent class extends the base Event by prohibiting clearing after signaling
    thus the name.
    """

    def clear(self) -> None:
        """Clears the event flag. This function will always raise a ThreadingException exception.
        """
        raise ThreadingException("OneTimeEvents cannot be cleared after signaling!") # pragma no cover