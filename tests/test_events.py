# pyright: basic
from pytest import raises as assert_raises, fixture
from time import sleep
from threading import Thread

from runtime.threading import Event, AutoClearEvent

def test_basic():
    ev1 = Event()
    ev2 = Event()
    ev3 = Event()
    ev4 = Event()
    Thread(target=waitX, args=(0.0005, ev2)).start()
    Thread(target=waitX, args=(0.1, ev1)).start()

    assert not Event.wait_all([ev1, ev2], timeout=0.01)
    assert Event.wait_any([ev1, ev2])
    assert Event.wait_all([ev1, ev2])
    assert ev1.wait()

    Thread(target=waitX, args=(0.02, ev4)).start()
    Thread(target=waitY, args=(ev4, ev3)).start()
    assert not ev3.wait(0)
    assert ev3.wait()
    assert ev3.wait(0)


def test_auto_clear_event():
    ev1 = AutoClearEvent()
    ev1.set()
    assert ev1.is_set
    ev1.wait()
    assert not ev1.is_set

    ev2 = AutoClearEvent()
    ev2.set()
    Event.wait_any([ev1,ev2])
    assert not ev2.is_set



def waitX(s: int, ev: Event):
    sleep(s)
    # print("setting event")
    ev.set()

def waitY(ev: Event, cb: Event):
    ev.wait()
    # print("event set")
    cb.set()

