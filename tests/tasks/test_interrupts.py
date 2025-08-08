# pyright: basic
# ruff: noqa
from pytest import raises as assert_raises, fixture

from runtime.threading.tasks import AggregateException
from runtime.threading import InterruptSignal, Interrupt, InterruptException

def test_basic(internals):
    cts = InterruptSignal()
    ct = cts.interrupt
    ct.raise_if_signaled()
    assert not ct.wait_event.wait(0)
    assert not cts.interrupt.is_signaled
    cts.signal()

    assert cts.interrupt.is_signaled
    assert ct.is_signaled

    with assert_raises(InterruptException):
        ct.raise_if_signaled()

    assert ct.wait(0)


def test_linked(internals):
    cts1 = InterruptSignal()
    cts2 = InterruptSignal()
    assert not cts1.interrupt.propagates_to(cts2.interrupt)
    assert not cts2.interrupt.propagates_to(cts1.interrupt)
    cts3 = InterruptSignal(cts1.interrupt, cts2.interrupt)

    assert not cts3.interrupt.is_signaled

    cts1.signal()

    assert cts3.interrupt.is_signaled

    cts2.signal()
    cts3.signal()

    cts1 = InterruptSignal()
    cts2 = InterruptSignal(cts1.interrupt)
    cts3 = InterruptSignal(cts2.interrupt)
    cts4 = InterruptSignal(cts3.interrupt)
    cts5 = InterruptSignal(cts4.interrupt)

    assert not cts5.interrupt.is_signaled

    cts1.signal()

    assert cts5.interrupt.is_signaled

    cts1 = InterruptSignal()
    cts2 = InterruptSignal()
    cts3 = InterruptSignal(cts1.interrupt, cts2.interrupt)
    cts4 = InterruptSignal(cts1.interrupt, cts2.interrupt, cts3.interrupt)
    cts5 = InterruptSignal(cts4.interrupt)
    cts6 = InterruptSignal(cts1.interrupt, cts2.interrupt, cts3.interrupt)
    cts7 = InterruptSignal(cts3.interrupt)

    assert cts1.interrupt.propagates_to(cts3.interrupt)
    assert cts2.interrupt.propagates_to(cts3.interrupt)
    assert cts2.interrupt.propagates_to(cts4.interrupt)
    assert cts2.interrupt.propagates_to(cts5.interrupt)
    assert not cts4.interrupt.propagates_to(cts1.interrupt)
    assert cts3.interrupt.propagates_to(cts7.interrupt)

def test_aggregate_exception(internals):
    ex1 = Exception("test1")
    ex2 = Exception("test2")
    aex1 = AggregateException((ex1, ex2))
    aex2 = AggregateException((aex1,))
    aex3 = AggregateException((ex1,))
    aex4 = AggregateException((aex3,))

    assert aex4.flatten() is ex1
    assert aex2.flatten() is aex1
    assert aex1.flatten() is aex1
    assert ex1 in aex1.exceptions and ex2 in aex1.exceptions

    with assert_raises(AggregateException):
        aex1.handle(lambda ex: ex is ex1)

    try:
        aex1.handle(lambda ex: ex is ex1)
    except AggregateException as aex:
        assert ex1 not in aex.exceptions
        assert ex2 in aex.exceptions
        assert aex.flatten() is ex2
        aex.handle(lambda ex: ex is ex2)
