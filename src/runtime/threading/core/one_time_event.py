from runtime.threading.core.event import Event
from runtime.threading.core.threading_exception import ThreadingException

class OneTimeEvent(Event):
    """An event that cannot be cleared after signaling.
    """

    def clear(self) -> None:
        raise ThreadingException("OnTimeEvent cannot be cleared after signaling!") # pragma no cover