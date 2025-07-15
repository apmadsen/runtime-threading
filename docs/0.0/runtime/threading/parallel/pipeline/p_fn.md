[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     [pipeline](/docs/0.0/runtime/threading/parallel/module.md) >
      PFn

# PFn[Tin, Tout]

The `PFn` class (short for Parallel Function) is the heart of the parallel pipelines. It uses  parallel.process() internally to process the work it's given and gets its parameters from the `PContext` parallel context.

## Constructors

### __init__(self, fn: _Callable[[[Task](../../tasks/task.md)[Iterable[Tout]], Tin], Iterable[Tout]]_)

Creates a new parallel function.

- fn `(Task[Iterable[Tout], Tin) -> Iterable[Tout]`: The target function to parallelize.

### __init__(self, fn: _Callable[[[Task](../../tasks/task.md)[Iterable[Tout]], Tin], Iterable[Tout]]_, parallelism: _int_)

Creates a new parallel function.

- fn `(Task[Iterable[Tout], Tin) -> Iterable[Tout]`: The target function to parallelize.
- parallelism `int`: A no between 1 and 32 representing the max no. of parallel threads.

### __init__(self, fn: _Callable[[[Task](../../tasks/task.md)[Iterable[Tout]], Tin], Iterable[Tout]]_, parallelism: _float_)

Creates a new parallel function.

- fn `(Task[Iterable[Tout], Tin) -> Iterable[Tout]`: The target function to parallelize.
- parallelism `float`: A no between 0.0 and 1.0 representing the no. of parallel threads relative to the max parallelism of the current `PContext`.
