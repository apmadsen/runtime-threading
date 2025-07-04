[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     [pipeline](/docs/0.0/runtime/threading/parallel/module.md) >
      PIterable

# PIterable[T] : Iterable[T], Protocol

The `PIterable` class is a protocol for parallel Iterables which allows for interruptable iterations with timeouts.

It's used throughout the `runtime.threading.parallel.pipeline` module and implemented by the `ProducerConsumerQueueIterator` class.

## Functions

### drain() -> _None_

Drains the `PIterable` from items.

### drain(timeout: _float | None_ = _None_, interrupt: _Interrupt | None_ = _None_) -> _None_

Drains the `PIterable` from items.

- timeout `float | None`: The no. of seconds to wait for new items before exiting operation. Defaults to `None`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.