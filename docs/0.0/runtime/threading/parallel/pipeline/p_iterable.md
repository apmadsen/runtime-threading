[Documentation](../../../../../documentation.md) >
 [v0.0](../../../../version.md) >
  [runtime](../../../module.md) >
   [threading](../../module.md) >
    [parallel](../module.md) >
     [pipeline](module.md) >
      PIterable

# PIterable[T] : Iterable[T], Protocol

The `PIterable` class is a protocol for parallel Iterables which allows for interruptable iterations with timeouts.

It's used throughout the `runtime.threading.parallel.pipeline` module and implemented by the `ProducerConsumerQueueIterator` class.

## Functions

### drain() -> _None_

Drains the `PIterable` from items.

### drain(timeout: _float | None_ = _None_, interrupt: _[Interrupt](../../interrupt.md) | None_ = _None_) -> _None_

Drains the `PIterable` from items.

- timeout `float | None`: The no. of seconds to wait for new items before exiting operation. Defaults to `None`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.