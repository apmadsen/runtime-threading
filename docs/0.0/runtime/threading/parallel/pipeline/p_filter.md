[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     [pipeline](/docs/0.0/runtime/threading/parallel/module.md) >
      PFilter

# PFilter[T, T] : [PFn](p_fn.md)[T, T]

The `PFilter` class is an extension of the base `PFn` class which applies a filter to the work items.
The function is inclusive, meaning is uses a predefined predicate function to select the items it lets through.

## Constructors

### \_\_init\_\_()

Creates a new catch-all parallel filter function, i.e. one that doesn't filter out anything.

### \_\_init\_\_(*, parallelism: _int_)

Creates a new catch-all parallel filter function, i.e. one that doesn't filter out anything.

- parallelism `int`: A no. between 1 and 32 representing the max no. of parallel threads.

### \_\_init\_\_(fn: _Callable[[[Task](../../tasks/task.md)[Iterable[T]], T], bool]_)

- fn `(Task[T], T) -> bool`: The predicate function used to to determine which items to let through.

### \_\_init\_\_(fn: _Callable[[[Task](../../tasks/task.md)[Iterable[T]], T], bool]_, *, parallelism: _int_)

- fn `(Task[T], T) -> bool`: The predicate function used to to determine which items to let through.
- parallelism `int`: A no. between 1 and 32 representing the max no. of parallel threads.

## Properties

### is_catch_all -> _bool_

Indicates if filter it a simple catch-all filter.