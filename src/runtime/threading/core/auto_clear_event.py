from runtime.threading.core.event import Event

class AutoClearEvent(Event):
    """ The AutoClearEvent class extends the basic Event by automatically clearing after being awaited.
    """

    def _after_wait(self) -> None:
        if self.is_signaled:
            super().clear()