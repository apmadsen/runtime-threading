[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     ForEachProto

# ForEachProto

The `ForEachProto` class is a wrapper used to create new for-each processes. The intended use is through the `foreach()` function.

## Constructors

### \_\_init\_\_(items: _Iterable[T]_, task_name: _str | None_ = _None_, parallelism: _int | None_ = _None_, interrupt: _[Interrupt](../interrupt.md) | None_ = _None_, scheduler: _[TaskScheduler](../tasks/schedulers/task_scheduler.md) | None_ = _None_)

- items `Iterable[T]`: The items to be processed.
- task_name `str | None`: The task name prefix. Defaults to `None`.
- parallelism `int | None` = The no. of parallel tasks to use. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel operation. Defaults to `None`.
- scheduler `TaskScheduler | None` = The task scheduler onto which tasks are sceduled. Defaults to `None`.

## Functions

### do(fn: _Callable[Concatenate[Task[None], T, P], None]_, /, *args: P.args, **kwargs: P.kwargs) -> _Task[None]_

Initiates parallel processing immediately.

- fn `(task: Task[None], T, P) -> Task[None]`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).
