# pyright: basic
from pytest import raises as assert_raises, fixture

from runtime.threading.tasks import InterruptException
from runtime.threading import InterruptSignal, Interrupt

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

    with assert_raises(InterruptException):
        ct.raise_if_signaled()
    assert ct.wait_event.wait(0)


def test_linked():
    cts1 = InterruptSignal()
    cts2 = InterruptSignal()
    cts3 = InterruptSignal(cts1.interrupt, cts2.interrupt)

    assert not cts3.is_signaled

    cts1.signal()

    assert cts3.is_signaled

    cts2.signal()
    cts3.signal()

    cts1 = InterruptSignal()
    cts2 = InterruptSignal(cts1.interrupt)
    cts3 = InterruptSignal(cts2.interrupt)
    cts4 = InterruptSignal(cts3.interrupt)
    cts5 = InterruptSignal(cts4.interrupt)

    assert not cts5.is_signaled

    cts1.signal()

    assert cts5.is_signaled

    cts1 = InterruptSignal()
    cts2 = InterruptSignal()
    cts3 = InterruptSignal(cts1.interrupt, cts2.interrupt)
    cts4 = InterruptSignal(cts2.interrupt, cts3.interrupt)
    cts5 = InterruptSignal(cts4.interrupt)

    assert cts1.interrupt.propagates_to(cts3.interrupt)
    assert cts2.interrupt.propagates_to(cts3.interrupt)
    assert cts2.interrupt.propagates_to(cts4.interrupt)
    assert cts2.interrupt.propagates_to(cts5.interrupt)

    x=0
