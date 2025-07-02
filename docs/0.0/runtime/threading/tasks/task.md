[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [tasks](/docs/0.0/runtime/threading/tasks/module.md) >
     Task

# Task

The `Task` class is an abstraction of a regular thread, and it represents an application task of work.

### Example

```python
from runtime.threading import InterruptSignal, InterruptException
from runtime.threading.tasks import Task

try:
     signal = InterruptSignal()
     i = 227
     m = 0.78

     def fn(task: Task[float], i: float, m: float) -> float:
          task.interrupt.raise_if_signaled()
          return i * m

     task = Task.create(interrupt = signal.interrupt, lazy = True).run(fn, i, m)

     result = task.result # -> 177.06

except InterruptException:
     pass
```

## Constructors

> Instead of using the constructer directly, use the functions `Task.Create()`, `Task.Plan()` and `Task.Run()` instead.

### \_\_init\_\_(fn: _Callable[[Task[T]], T]_, name: _str | None_ = _None_, interrupt: _Interrupt | None_ = _None_, lazy: _bool_ = _False_)

- fn `(task: [Task[T]) -> T`: The function which will be called to do the work.
- name `str | None`: The name of the task (and the underlying thread). Defaults to `None`.
- interrupt `Interrupt | None`: The external interrupt. Defaults to `None`.
- lazy `bool`: Specifies whether or not the task may be run lazily when awaited. Defaults to False.

Note: If task was created without, `Interrupt.none()` is used.

## Properties

### id -> _int_

The task's internal id.

### name -> _str_

Gets or sets the tasks name

### state -> _TaskState_

The tasks internal state.

### parent -> _Task[Any]_

The parent task (if any).

### target -> _str_

Returns the name of the target function (for testing).

### is_completed -> _bool_

Indicates if the task is completed or not.

### is_completed_successfully -> _bool_

Indicates if the task is successfully completed (ie. ran to end without any exceptions).

### is_failed -> _bool_

Indicates if the target function raised an exception.

### is_interrupted -> _bool_

Indicates if task was interrupted or not. Only tasks which raises an `InterruptException` generated from `Interrupt.raise_if_interrupted()` method, and from the same `InterruptSignal` are considered interrupted. Simply raising an `interruptExecption` will cause task to fail.

### is_scheduled -> _bool_

Indicates if the task is scheduled to run.

### is_running -> _bool_

Indicates if the task is running.

### is_lazy -> _bool_

Indicates if task is lazy. If it is, task will be scheduled automatically when awaited, or when property `Task.result` is accessed.

### interrupt -> _Interrupt_

The task interrupt. Note: If task was created without, `Interrupt.none()` is used.

### result -> _T_

The result of the task (if any). This call will block until task is done, and if target function raised an exception, that exception will be re-raised here. If task is not scheduled and is lazy, it will be run automatically.

### exception -> _Exception | None_

The exception raised by target function (if any).

### wait_event -> _Event_

The internal task event, signaled upon completion.

### current -> _Task[Any] | None_

Returns the currently running task, if called from within one.

## Functions

### schedule(scheduler: _TaskScheduler | None_ = _None_) -> _None_

Queues the task on the specified scheduler. If scheduler is omitted or None, the current or default task scheduler is used (ie. `TaskScheduler.current()`).

- scheduler `TaskScheduler`: The task scheduler on which to schedule. Defaults to `None`.

### run_synchronously() -> _None_

Runs the task synchronously.

### wait(timeout: _float | None_, interrupt: _Interrupt | None_) -> _bool_

Waits for the task to complete. If task has not been scheduled and is lazy, it will be run automatically.

- timeout `float | None`: The no. of seconds to wait before returning `False`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.

Returns `True` if task completed, `False` otherwise.

### continue_with(options: _ContinuationOptions_, fn: _Callable[[Task[Tcontinuation], Task[T], P], Tcontinuation]_, /, *args: P.args, **kwargs: P.kwargs) -> _Task[Tcontinuation]_

Creates and returns a continuation task which is run when this task transitions into a state matched by that specified in 'options' argument.

- options `ContinuationOptions`: Specifies when and how continuation is run.
- fn: `(task: Task[Tcontinuation], preceding_task: Task[T], P) -> Tcontinuation`: The targetfunction.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### Example

```python
from runtime.threading.tasks import Task, ContinuationOptions

i = 227
m = 0.78

def fn(task: Task[float], i: float, m: float) -> float:
     return i * m

def fn_continue(task: Task[float], preceding_task: Task[float], m: float) -> float:
     return preceding_task.result * m

task1 = Task.run(fn, i, m)
task2 = task1.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY, fn_continue, m)

result1 = task1.result # -> 177.06
result2 = task2.result # -> 138.1068
```

## Static functions

### wait_any(tasks: _Sequence[Task[Any]]_, timeout: _float | None_ = _None_, /,fail_on_interrupt: _bool_ = _False_, interrupt: _Interrupt | None_ = _None_) -> _bool_

Waits for any of the specified tasks to complete. Returns true when any of the tasks completed. Otherwise False.

- tasks `Sequence[Task]`: The tasks to await.
- timeout `float | None`: Timeout (seconds) before returning False. Defaults to `None`.
- fail_on_interrupt `bool`: Raise an `AwaitedTaskInterruptedError` if any of the tasks was interrupted.
- interrupt `Interrupt | None`: An Interrupt for this specific call. Defaults to `None`.

### wait_all(tasks: _Sequence[Task[Any]]_, timeout: _float | None_ = _None_, /,fail_on_interrupt: _bool_ = _False_, interrupt: _Interrupt | None_ = _None_) -> _bool_

Waits for all of the specified tasks to complete. Returns true if all of the tasks completed. Otherwise False.

- tasks `Sequence[Task]`: The tasks to await.
- timeout `float | None`: Timeout (seconds) before returning False. Defaults to `None`.
- fail_on_interrupt `bool`: Raise an `AwaitedTaskInterruptedError` if any of the tasks was interrupted.
- interrupt `Interrupt | None`: An Interrupt for this specific call. Defaults to `None`.

### with_any(tasks: _Sequence[Task[Any]]_, /, options: _ContinuationOptions_ = _ContinuationOptions.ON_COMPLETED_SUCCESSFULLY_, interrupt: _Interrupt | None_ = _None_) -> _ContinuationProto_

Initiates the creation of a new continuation which is run when any of the specified tasks are completed. Returns a `ContinuationProto` wrapper.

- tasks `Sequence[Task]`: The tasks to await.
- options `ContinuationOptions`: Specifies when and how continuation is run. Defaults to `ON_COMPLETED_SUCCESSFULLY`
- interrupt `Interrupt | None`: An Interrupt for this specific call. Defaults to `None`.

### with_all(tasks: _Sequence[Task[Any]]_, /, options: _ContinuationOptions_ = _ContinuationOptions.ON_COMPLETED_SUCCESSFULLY_, interrupt: _Interrupt | None_ = _None_) -> _ContinuationProto_

Initiates the creation of a new continuation which is run when all of the specified tasks are completed. Returns a `ContinuationProto` wrapper.

- tasks `Sequence[Task]`: The tasks to await.
- options `ContinuationOptions`: Specifies when and how continuation is run. Defaults to `ON_COMPLETED_SUCCESSFULLY`
- interrupt `Interrupt | None`: An Interrupt for this specific call. Defaults to `None`.


### Example

```python
from typing import Sequence
from runtime.threading.tasks import Task, ContinuationOptions

i = 227
m = 0.78

def fn(task: Task[float], i: float, m: float) -> float:
     return i * m

def fn_continue(task: Task[float], preceding_tasks: Sequence[Task[float]]) -> float:
     return sum(( task.result for task in preceding_tasks ))

tasks = [ Task.run(fn, i, m) for x in range(5) ]
task = Task.with_all(tasks, ContinuationOptions.DEFAULT).run(fn_continue)

result = task.result # -> 885.3
```

### create(*, name: _str | None_ = _None_, interrupt: _Interrupt | None_ = _None_, scheduler: _TaskScheduler | None_ = _None_, lazy: _bool_ = _False_) -> _TaskProto_

Initiates the creation of a new Task. Returns a `TaskProto` wrapper.

- name `str | None`: The name if the task. Defaults to `None`.
- interrupt `Interrupt | None`: An external interrupt used to stop the task. Defaults to `None`.
- scheduler `TaskScheduler | None`: A scheduler onto which the task will be scheduled. Defaults to `None`.
- lazy `bool`: Specifies if task can be lazily started or not. Defaults to `False`.

### plan(fn: _Callable[[Task[Tresult], P], Tresult]_, /, *args: _P.args_, **kwargs: _P.kwargs_) -> _Task[Tresult]_

Creates a new task without scheduling it. Use `Task.Create().plan()` for more control of the task specifics. Returns a new task.

- fn `(task: Task[Tresult], P) -> Tresult`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### run(fn: _Callable[[Task[Tresult], P], Tresult]_, /, *args: _P.args_, **kwargs: _P.kwargs_) -> _Task[Tresult]_

Creates a new task and schedules it on the default scheduler. Use `Task.Create().run()` for more control of the task specifics. Returns a new task.

- fn `(task: Task[Tresult], P) -> Tresult`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### run_after(time: _float_, fn: _Callable[[Task[Tresult], P], Tresult]_, /, *args: _P.args_, **kwargs: _P.kwargs_) -> _Task[Tresult]_

Creates a new task which will be scheduled on the default scheduler after specified time. Use `Task.Create().run_after()` for more control of the task specifics. Returns a new task.

- time `float`: The time in seconds to wait before scheduling the task:
- fn `(task: Task[Tresult], P) -> Tresult`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### from_result(result: _Tresult_) -> _Task[Tresult]_

Creates and returns a task which is completed with a preset result.

- result `Tresult`: The predefined result.


```python
from runtime.threading.tasks import Task

task = Task.from_result("abc") # -> Task[str]
result = task.result # -> "abc"
```