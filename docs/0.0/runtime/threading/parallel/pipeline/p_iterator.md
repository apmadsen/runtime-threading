[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     [pipeline](/docs/0.0/runtime/threading/parallel/module.md) >
      PIterator

# PIterator[T] : Iterator[T], Protocol

The `PIterator` class is a protocol for parallel iterators which allows for interruptable iterations with timeouts.

It's used throughout the `runtime.threading.parallel.pipeline` module and implemented by the `ProducerConsumerQueueIterator` class.

## Functions

### next(timeout: _float | None_ = _None_, interrupt: _Interrupt | None_ = _None_) -> _T_

- timeout `float | None`: The no. of seconds to wait for new items before raising a StopIteration exception. Defaults to `None`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.