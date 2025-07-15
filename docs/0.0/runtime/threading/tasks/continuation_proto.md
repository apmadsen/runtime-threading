[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [tasks](/docs/0.0/runtime/threading/tasks/module.md) >
     TaskProto

# ContinuationProto

The `ContinuationProto` class is a wrapper used to create task continuations. The intended use is through the `Task.witl_all()` and `Task.witl_any()` functions.

## Constructors

### \_\_init\_\_(tasks: _Sequence[Task[Any]]_, when: _[ContinueWhen](../continuation_when.md)_, /, options: _[ContinuationOptions](continuation_options.md)_ = _ContinuationOptions.ON_COMPLETED_SUCCESSFULLY_, name: _str | None_ = _None_, interrupt: _[Interrupt](interrupt.md) | None_ = _None_)

Creates a `ContinuationProto` instance which can be used for creating task continuations.

- tasks `Sequence[Task[Any]]`: The tasks to which a continuation will be created.
- when `ContinueWhen`: Specifies whether all tasks must be completed or just one before continuation is executed.
- name `str | None`: The task name. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel task(s). Defaults to `None`.

## Functions

### plan(fn: _Callable[Concatenate[Task[Tresult], P], Tresult]_, *args: P.args, **kwargs: P.kwargs) -> _Task[Tresult]_

Creates a new task without scheduling it.

- fn `(task: Task[Tresult], P) -> Tresult`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### run(fn: _Callable[Concatenate[Task[Tresult], P], Tresult]_, *args: P.args, **kwargs: P.kwargs) -> _Task[Tresult]_

Creates a new task and schedules it.

- fn `(task: Task[Tresult], P) -> Tresult`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).
