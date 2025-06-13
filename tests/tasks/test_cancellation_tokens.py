# pyright: basic
from pytest import raises as assert_raises, fixture

from runtime.threading.tasks import InterruptSignal, Interrupt, TaskInterruptException

def test_basic():
    cn = Interrupt.none()
    cn.raise_if_signaled()

    cts = InterruptSignal()
    ct = cts.interrupt
    ct.raise_if_signaled()
    assert not ct.wait_event.wait(0)
    cts.signal()
    assert cts.is_signaled
    assert ct.is_signaled

    with assert_raises(TaskInterruptException):
        ct.raise_if_signaled()
    assert ct.wait_event.wait(0)


def test_linked():
    cts1 = InterruptSignal()
    cts2 = InterruptSignal()
    cts3 = InterruptSignal(cts1.interrupt, cts2.interrupt)
    cts1.signal()
    assert cts3.is_signaled
    cts2.signal()
