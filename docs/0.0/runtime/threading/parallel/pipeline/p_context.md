[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     [pipeline](/docs/0.0/runtime/threading/parallel/module.md) >
      PContext

# PContext

The `PContext` class is used for setting up parallel contexts which in turn provides parallelism options, interrupts and schedulers to parallel pipelines.

## Constructors

### \_\_init\_\_(max_parallelism: _int_, /)

Creates a new parallel context.

- max_parallelism `int`: The maximum no. of parallel threads.

### \_\_init\_\_(max_parallelism: _int_, /, interrupt: _[Interrupt](../../interrupt.md) | None_ = _None_, scheduler: _[TaskScheduler](../../tasks/schedulers/task_scheduler.md) | None_ = _None_)

Creates a new parallel context.

- max_parallelism `int`: The maximum no. of parallel threads.
- interrupt `Interrupt | None`: An external interrupt used to stop parallel processes. Defaults to `None`.
- scheduler `TaskScheduler | None`: A scheduler onto which the parallel process tasks will be scheduled. Defaults to `None`.

## Properties

### id -> _int_

The ID of the PContext instance.

### max_parallelism -> _int_

The max degree of parallelism a parallel operation should use.

### scheduler -> _ [TaskScheduler](../../tasks/schedulers/task_scheduler.md)_

The scheduler for internal tasks.

# interrupt -> _ [Interrupt](../../interrupt.md)_

The external Interrupt used to interrupt a parallel operation.

## Static functions

### root() -> _PContext_

Returns the root parallel context. This is created automatically on a per-thread basis.

### current() -> _PContext_

Returns the current parallel context. Defaults to the root context.

