[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     ProducerConsumerQueueIterator

# ProducerConsumerQueueIterator : PIterator[T]

The `ProducerConsumerQueueIterator` class is used to create an iterator over a `ProducerConsumerQueue` instance. Under normal use it acts like a normal iterator, but when used through the various functions and classes in the `runtime.threading.parallel` module, it supports timeout and interrupts when calling `next()`.

## Constructors

### \_\_init\_\_(queue: _ProducerConsumerQueue[T]_)

Creates a new `ProducerConsumerQueueIterator` instance linked to the specified `ProducerConsumerQueue`.

- queue: `ProducerConsumerQueue[T]`: The queue to iterate over.

## Functions

### next(timeout: _float | None_ = _None_, interrupt: _Interrupt | None_ = _None_) -> _T_:

Takes an item from the linked `ProducerConsumerQueue`.

- timeout `float | None`: Timeout (seconds) before raising a `StopIteration` exception thus stopping the object iterating. Defaults to `None`.
- interrupt `Interrupt | None`: An Interrupt for this specific call. Defaults to `None`.