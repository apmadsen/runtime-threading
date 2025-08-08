# pyright: basic
# ruff: noqa
from pytest import raises as assert_raises, fixture
from time import sleep
from typingutils import get_type_name
from threading import Thread

from runtime.threading import Event, AutoClearEvent, InterruptSignal, Interrupt
from runtime.threading.core.defaults import TASK_SUSPEND_AFTER, POLL_INTERVAL
from runtime.threading.core.event_continuation import EventContinuation
from runtime.threading.core.continue_when import ContinueWhen

from tests.shared_functions import (
    fn_wait_for_event_and_set_another, fn_sleep_and_set_event
)


def test_basic(internals):
    ev1 = Event()
    ev2 = Event()
    ev3 = Event()
    ev4 = Event()
    ev5 = Event()

    signal1 = InterruptSignal()
    signal2 = InterruptSignal()
    signal1.signal()

    assert not ev1.is_signaled
    ev5.signal()
    assert ev5.is_signaled

    assert not ev1.wait(0, interrupt = signal2.interrupt)
    assert not ev1.wait(interrupt = signal1.interrupt)

    Thread(target=fn_sleep_and_set_event, args=(0.0005, ev2)).start()
    Thread(target=fn_sleep_and_set_event, args=(0.1, ev1)).start()

    assert not Event.wait_all([ev1, ev2], 0.01)
    assert Event.wait_any([ev1, ev2])
    assert Event.wait_all([ev1, ev2])
    assert ev1.wait(interrupt = signal2.interrupt)

    Thread(target=fn_sleep_and_set_event, args=(0.02, ev4)).start()
    Thread(target=fn_wait_for_event_and_set_another, args=(None, ev4, ev3)).start()
    assert not ev3.wait(0)
    assert ev3.wait()
    assert ev3.wait(0)

def test_interrupts(internals):
    ev1 = Event()
    ev2 = Event()


    signal1 = InterruptSignal()
    signal2 = InterruptSignal()

    assert not Event.wait_any((ev1,ev2), 0, interrupt=signal1.interrupt)
    assert not Event.wait_all((ev1,ev2), 0, interrupt=signal1.interrupt)

    signal1.signal()
    assert not Event.wait_any((ev1,ev2), 0, interrupt=signal1.interrupt)
    assert not Event.wait_all((ev1,ev2), 0, interrupt=signal1.interrupt)

    ev1.signal()
    assert Event.wait_any((ev1,ev2), 0, interrupt=signal2.interrupt)
    assert not Event.wait_all((ev1,ev2), 0, interrupt=signal2.interrupt)

    ev2.signal()
    assert Event.wait_any((ev1,ev2), 0, interrupt=signal2.interrupt)
    assert Event.wait_all((ev1,ev2), 0, interrupt=signal2.interrupt)

    signal2.signal()
    assert not Event.wait_any((ev1,ev2), 0, interrupt=signal2.interrupt)
    assert not Event.wait_all((ev1,ev2), 0, interrupt=signal2.interrupt)





def test_task_suspend(internals):
    ev1 = Event()
    ev2 = Event()
    Thread(target=fn_sleep_and_set_event, args=(POLL_INTERVAL*2, ev1)).start()

    t = Thread(target=fn_wait_for_event_and_set_another, args=(TASK_SUSPEND_AFTER*2, ev1, ev2))
    t.start()
    t.join()
    assert ev2.is_signaled


def test_auto_clear_event():
    ev1 = AutoClearEvent()
    ev1.signal()
    assert ev1.is_signaled
    ev1.wait()
    assert not ev1.is_signaled

    ev2 = AutoClearEvent()
    ev2.signal()
    Event.wait_any([ev1,ev2])
    # assert ev2.is_signaled # ev1 will propagate first
    # ev2.wait()
    assert not ev2.is_signaled



def test_multiple_auto_clear_events():
    ev1 = AutoClearEvent()
    ev2 = AutoClearEvent()

    combined_event = Event(purpose = "CONTINUATION")

    Event._add_continuation(
        (ev1, ev2),
        EventContinuation(
            ContinueWhen.ALL,
            (ev1, ev2),
            combined_event,
            Interrupt.none()
        )
    )

    ev1.signal()
    assert ev1.is_signaled # because only one event was signaled, the continuation isn't expedited

    ev2.signal() # now the continuation is expedited
    assert not ev1.is_signaled
    assert not ev2.is_signaled

    x=0

