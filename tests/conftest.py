# pyright: basic
from os import getenv
from typing import Any, Iterable, cast
from pytest import fixture
from typingutils import get_type_name
from threading import Thread, Event

from runtime.threading.core.event import terminate_event
from runtime.threading.core.continuation import Continuation
from runtime.threading.core.tasks.helpers import get_function_name
from runtime.threading.core.tasks.schedulers.concurrent_task_scheduler import ConcurrentTaskScheduler
from runtime.threading.core.testing.debug import enable_debugging, EventsDebugger, LocksDebugger
from runtime.threading.core.tasks.schedulers.task_scheduler import LOCK as TASK_LOCK, THREADS, TaskScheduler

EVENTS_DEBUGGER: EventsDebugger | None = None
LOCKS_DEBUGGER: LocksDebugger | None = None

@fixture(scope = "package")
def internals():
    if bool(getenv("TEST_DEBUG")):
        global EVENTS_DEBUGGER, LOCKS_DEBUGGER
        EVENTS_DEBUGGER, LOCKS_DEBUGGER = enable_debugging()

        ev = Event()

        def fn_report():
            ev.wait(20)
            if not ev.is_set():
                report()

        Thread(target=fn_report, args=()).start()

    yield

    if bool(getenv("TEST_DEBUG")):
        if not ev.is_set():
            ev.set()
            report()

def get_type_name_short(cls: type) -> str:
    return get_type_name(cls).rsplit(".", maxsplit=1)[-1]

def get_referrer(obj: Any) -> tuple[str] | None:
    if hasattr(obj, "__referrer__"):
        referrer = getattr(obj, "__referrer__")
        if callable(referrer):
            referrer = tuple( line.strip() for line in cast(str, referrer()).split("->") )
            setattr(obj, "__referrer__", referrer)
        return cast(tuple[str], referrer)
    return None

def format_referrer(obj: Any, indent: int) -> str:
    if referrer := get_referrer(obj):
        return "".join((
            "\n" + ("  "*indent) + line.strip()
            for line in referrer
        ))
    else:
        return "  "*indent + "Unknown"

def report():
    terminate_event.wait(1)
    print("\n")
    report_tasks()
    report_locks()
    report_events()
    report_continuations()

def report_locks():
    if not LOCKS_DEBUGGER or not (waits := LOCKS_DEBUGGER.get_waits()):
        print("\n-- LOCK WAITS: NONE")
    else:
        print("\n-- LOCK WAITS:")

        for lock, items in waits.items():
            print(f"  {id(lock)} : {items}")
            # print(f"  {id(lock)} ->")
            # for item in items:
            #     print(f"    {item}")

def report_events():
    if not EVENTS_DEBUGGER or not (waits := EVENTS_DEBUGGER.get_waits()):
        print("\n-- EVENT WAITS: NONE")
    else:
        print("\n-- EVENT WAITS:")

        for lock, items in waits.items():
            print(f"  {id(lock)} : {items}")
            # print(f"  {id(lock)} ->")
            # for item in items:
            #     print(f"    {item}")


def filter_continuations(continuations: dict[Event, set[Continuation]]) -> dict[Event, set[Continuation]]:
    result: dict[Event, set[Continuation]] = {}
    for event, continuations1 in continuations.items():
        remaining: set[Continuation] = set()
        for continuation in continuations1:
            if referrer := get_referrer(continuation):
                if referrer[0].startswith("concurrent_task_scheduler.py") and referrer[0].endswith("(__run)"):
                    pass # filter out ConcurrentTaskScheduler waiting tasks
                else:
                    remaining.add(continuation)
            else:
                remaining.add(continuation)

        if remaining:
            result[event] = remaining

    return result


def report_continuations():
    if not EVENTS_DEBUGGER or not (continuations := EVENTS_DEBUGGER.get_continuations()) or not ( continuations := filter_continuations(continuations) ): # pyright: ignore[reportArgumentType]
        print("\n-- CONTINUATIONS: NONE")
    else:
        print("\n-- CONTINUATIONS:")
        for continuation in set( continuation for _, continuations in continuations.items() for continuation in continuations ):
            print(f"  {get_type_name_short(type(continuation))} {id(continuation)} {format_referrer(continuation, 2)} ->")
            if continuation.events:
                print("")
                for cont_event in tuple(continuation.events):
                    print(f"    EVENT {id(getattr(cont_event, '_Event__internal_event'))} : {cont_event.is_signaled} ->")
                    if event_continuations := tuple(str(id(continuation1)) for continuation1 in getattr(cont_event, "_Event__continuations")):
                        print("      " + (", ".join(event_continuations)))


def report_tasks():
    with TASK_LOCK:
        schedulers = {
            scheduler: (thread, task)
            for thread, (scheduler, task) in THREADS.items()
            if not task or not task.is_completed
        }
        if schedulers:
            print("\n-- TASKS:")
            for scheduler, (thread, task) in schedulers.items():
                print(f"  SCHEDULER {id(scheduler)} :")
                if task:
                    print(f"   {thread.name} ->")
                    print(f"     {task.id} : {task.state.name}")
                else:
                    print(f"   {thread.name} -> No task")
        else:
            print("\n-- TASKS: NONE")
