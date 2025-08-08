# pyright: basic
# ruff: noqa
from pytest import raises as assert_raises, fixture
from typing import Any, cast
from time import sleep
from datetime import datetime
from time import time

from runtime.threading import InterruptSignal, Lock, acquire_or_fail, signal_after

def test_signal_after():
    sig = InterruptSignal()
    st = time()
    signal_after(sig, 0.025)
    assert time()-st > 0.025

def test_acquire_or_fail():
    lock = Lock(False)

    with acquire_or_fail(lock, 10, lambda: Exception()):
        pass

    lock.acquire()

    with assert_raises(Exception, match="notacquired"):
        with acquire_or_fail(lock, 0.01, lambda: Exception("notacquired")):
            pass