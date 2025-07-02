[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     ProcessProto

# ProcessProto

The `ProcessProto` class is a wrapper used to create new processes. The intended use is through the `process()` function.

## Constructors

### \_\_init\_\_(items: _Iterable[Tin]_, task_name: _str | None_ = _None_, parallelism: _int | None_ = _None_, interrupt: _Interrupt | None_ = _None_, scheduler: _TaskScheduler | None_ = _None_)

- items `Iterable[Tin]`: The items to be processed.
- task_name `str | None`: The task name prefix. Defaults to `None`.
- parallelism `int | None` = The no. of parallel tasks to use. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel operation. Defaults to `None`.
- scheduler `TaskScheduler | None` = The task scheduler onto which tasks are sceduled. Defaults to `None`.

## Functions

### do(fn: _Callable[Concatenate[Task[Iterable[Tout]], Tin, P], Iterable[Tout]]_, /, *args: P.args, **kwargs: P.kwargs) -> _PIterable[Tout]_

Initiates parallel processing immediately.

- fn `(task: Task[Iterable[Tout]], Tin, P) -> Iterable[Tout]`: The target function.
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).

### do(fn: _Callable[Concatenate[Task[Iterable[Tout]], Tin, P], Iterable[Tout]]_, /, output_queue: _ProducerConsumerQueue[Tout]_, *args: P.args, **kwargs: P.kwargs) -> _Task[None]_

Initiates parallel processing immediately and outputs data to an existing queue.

- fn `(task: Task[Iterable[Tout]], Tin, P) -> Iterable[Tout]`: The target function.
- output_queue `ProducerConsumerQueue[Tout]`
- *args `P.args`: The positional target arguments (if any).
- **kwargs `P.kwargs`: The keyword target arguments (if any).