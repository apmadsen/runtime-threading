from runtime.threading.core.tasks.event import Event

class AutoClearEvent(Event):
    """An event that is automatically cleared after continuations have been notified
    """
    def _after_wait(self) -> None:
        if self.is_set:
            Event.clear(self)