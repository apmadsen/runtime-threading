[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [tasks](/docs/0.0/runtime/threading/tasks/module.md) >
     TaskProto

# TaskProto

The `TaskProto` class is a wrapper used to create new tasks. The intended use is through the `Task.create()` function.

## Constructors

### \_\_init\_\_(name: _str | None_ = _None_, interrupt: _[Interrupt](interrupt.md) | None_ = _None_, scheduler: _[TaskScheduler](schedulers/task_scheduler.md) | None_ = _None_, lazy: _bool | None_ = _None_)

Creates a `TaskProto` instance which can be used for creating tasks.

- name `str | None`: The task name. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel task(s). Defaults to `None`.
- scheduler `TaskScheduler | None` = The task scheduler onto which created task(s) are sceduled. Defaults to `None`.
- lazy `bool | None`: Specifies whether or not the task may be run lazily when awaited. Defaults to `None`.

## Functions

### plan(fn: _Callable[Concatenate[Task[T], P], T]_, *args: P.args, **kwargs: P.kwargs) -> _Task[T]_

Creates a new task without scheduling it.

- fn `(task: Task[T], P) -> T`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### run(fn: _Callable[Concatenate[Task[T], P], T]_, *args: P.args, **kwargs: P.kwargs) -> _Task[T]_

Creates a new task and schedules it.

- fn `(task: Task[T], P) -> T`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### run_after(fn: _Callable[Concatenate[Task[T], P], T]_, *args: P.args, **kwargs: P.kwargs) -> _Task[T]_

Creates a new task which will be scheduled after specified time.

- time `float`: The time (seconds) to wait before scheduling the task.
- fn `(task: Task[T], P) -> T`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).