# pyright: basic
# ruff: noqa
from typing import Any, Sequence

from runtime.threading.tasks import Task, TaskState
from runtime.threading.tasks.schedulers import TaskScheduler
from runtime.threading import Interrupt, InterruptSignal, Event, Lock, Semaphore

def fn_return_value(task: Task[int], value: int) -> int:
    return value

def fn_return_value_after_time(task: Task[str], t_sleep: float, value: str) -> str:
    task.interrupt.wait_event.wait(t_sleep)
    task.interrupt.raise_if_signaled()
    return value

def fn_return_task(task: Task[Any]) -> Task[Any] | None:
    return task.current()

def fn_return_parent_task(task: Task[Any]) -> Task[Any] | None:
    assert task.current()
    def fn_child(task: Task[Any]) -> Task[Any] | None:
        return task.parent
    return Task.run(fn_child).result

def fn_interrupt_and_wait_for_task(task: Task[Any], interrupt: InterruptSignal, other: Task[Any]):
    interrupt.signal()
    other.wait()

def fn_wait_for_signal(task: Task[Any], interrupt: Interrupt, started_event: Event):
    started_event.signal()
    Event.wait_any((task.interrupt.wait_event, interrupt.wait_event))
    task.interrupt.raise_if_signaled()

def fn_raise_interrupt(task: Task[str], signal: InterruptSignal):
    signal.signal()
    task.interrupt.raise_if_signaled()

def fn_wait_for_task_after_time(task: Task[Any], other_task: Task[Any], t_sleep: float) -> None:
    task.interrupt.wait_event.wait(t_sleep)
    other_task.wait()

def fn_schedule_task_after_time(task: Task[Any], other_task: Task[Any], scheduler: TaskScheduler, t_sleep: float) -> None:
    task.interrupt.wait_event.wait(t_sleep)
    other_task.schedule(scheduler)

def fn_raise_unrelated_signal(task: Task[Any]):
    sig = InterruptSignal()
    sig.signal()
    sig.interrupt.raise_if_signaled()

def fn_fail_immediately(task: Task[str], error: str) -> str:
    raise Exception(error)

def fn_fail_after_time(task: Task[Any], t_sleep: float, error: str) -> None:
    task.interrupt.wait_event.wait(t_sleep)
    raise Exception(error)

def fn_get_first_result_from_tasks(task: Task[str | None], tasks: Sequence[Task[Any]]) -> str | None:
    for task in tasks:
        if task.is_completed:
            return task.result

def fn_get_count_of_tasks(task: Task[int], tasks: Sequence[Task[Any]]) -> int:
    return len(tasks)

def fn_sleep_if_not_interrupted(task: Task[Any], t_sleep: float) -> None:
    task.interrupt.raise_if_signaled()
    task.interrupt.wait_event.wait(t_sleep)

def fn_raise_interrupt_after_time(task: Task[Any], t_sleep: float):
    task.interrupt.wait_event.wait(t_sleep)
    task.interrupt.raise_if_signaled()

def fn_continue_and_return_result_or_state(task: Task[str], other_task: Task[str]) -> str:
    if other_task.is_lazy:
        _ =other_task.result

    if other_task.state != TaskState.COMPLETED:
        return other_task.state.name
    else:
        return other_task.result

def fn_continue_and_return_result_or_state_with_mods(task: Task[str], other_task: Task[str], x: int, *, y: int) -> str:
    if other_task.state != TaskState.COMPLETED:
        return other_task.state.name + " " + str(x*y)
    else:
        return other_task.result + " " + str(x*y)

def fn_acquire_signal_and_sleep(task: Task[Any], lock: Lock, acquired_event: Event, released_event: Event, t_sleep: float) -> None:
    with lock:
        acquired_event.signal()
        task.interrupt.wait_event.wait(t_sleep)
    released_event.signal()

def fn_signal_after_time(task: Task[Any], signal: InterruptSignal, t_sleep: float) -> None:
    task.interrupt.wait_event.wait(t_sleep)
    signal.signal()

def fn_wait_for_event_and_set_another(wait_timeout: float | None, wait_event: Event, callback: Event):
    wait_event.wait(wait_timeout)
    callback.signal()


def fn_sleep_and_set_event(t_sleep: float, callback: Event):
    callback.wait(t_sleep)
    callback.signal()

def fn_wait_until_scheduled_and_return_result(task: Task[float], other_task: Task[Any]) -> Any:
    while not other_task.is_scheduled:
        task.interrupt.wait_event.wait(0.1)
    return other_task.result # this will unqueue task t and run it synchronously

