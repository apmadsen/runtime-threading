# pyright: basic
from os import getenv
from typing import cast
from pytest import fixture
from typingutils import get_type_name
from threading import Thread, Event

from runtime.threading.core.tasks.helpers import get_function_name
from runtime.threading.core.tasks.schedulers.task_scheduler import LOCK as TASK_LOCK, THREADS, TaskScheduler
from runtime.threading.core.tasks.schedulers.concurrent_task_scheduler import ConcurrentTaskScheduler
from runtime.threading.core.event import LOCK as EVENT_LOCK, DEBUG_CONTINUATIONS, DEBUG_INT_WAITS
from runtime.threading.core.lock_base import LOCK as LOCK_LOCK, DEBUG_INT_WAITS as LOCK_DEBUG_INT_WAITS
from runtime.threading.tasks import Task, run_after
from runtime.threading import InterruptSignal

def report():
    print("\n")
    report_locks()
    report_events()
    report_continuations()
    report_tasks()

def report_locks():
    with EVENT_LOCK:
        if LOCK_DEBUG_INT_WAITS:
            print("\n-- LOCK WAITS:")

            for lock, count in LOCK_DEBUG_INT_WAITS.items():
                print(f"\t{id(lock)} : {count}")
        else:
            print("\n-- LOCK WAITS: NONE")

def report_events():
    with EVENT_LOCK:
        if DEBUG_INT_WAITS:
            print("\n-- EVENT WAITS:")

            for event, count in DEBUG_INT_WAITS.items():
                print(f"\t{id(event)} : {count}")
        else:
            print("\n-- EVENT WAITS: NONE")


def report_continuations():
    with EVENT_LOCK:
        if not DEBUG_CONTINUATIONS:
            print("\n-- CONTINUATIONS: NONE")
        else:
            print("\n-- CONTINUATIONS:")
            for continuation in set( continuation for _, continuations in DEBUG_CONTINUATIONS.items() for continuation in continuations ):
                print(f"{get_type_name(type(continuation))} {id(continuation)} ->")
                for cont_event in continuation.events:
                    print(f"\tEVENT {cont_event.id} : {cont_event.is_signaled} ->")
                    for continuation1 in getattr(cont_event, "_Event__continuations"):
                        print(f"\t\t{get_type_name(type(continuation))} {id(continuation1)}")

def report_tasks():
    with TASK_LOCK:
        schedulers = {
            scheduler: (thread, task)
            for thread, (scheduler, task) in THREADS.items()
        }
        if schedulers:
            print("\n-- TASKS:")
            for scheduler, (thread, task) in schedulers.items():
                print(f"\tSCHEDULER {scheduler.id} :")
                if isinstance(scheduler, ConcurrentTaskScheduler):
                    threads = cast(tuple[Thread], getattr(scheduler, "_ConcurrentTaskScheduler__active_threads"))
                    for thread in threads:
                        target = get_function_name(getattr(thread, "_target"))
                        if not target.endswith("concurrent_task_scheduler.__run"):
                            x=0

                if task:
                    print(f"\t {thread.name} ->")
                    print(f"\t\t {task.id} : {task.state.name}")
                else:
                    print(f"\t {thread.name} -> No task")
        else:
            print("\n-- TASKS: NONE")


@fixture(scope = "package")
def internals():
    if bool(getenv("TEST_DEBUG")):
        import runtime.threading.core.event as event_module
        event_module.DEBUG = True
        import runtime.threading.core.lock_base as lock_module
        lock_module.DEBUG = True

        ev = Event()

        def fn_report():
            ev.wait(10)
            if not ev.is_set():
                report()

        Thread(target=fn_report, args=()).start()

    yield

    if bool(getenv("TEST_DEBUG")):
        if not ev.is_set():
            ev.set()
            report()