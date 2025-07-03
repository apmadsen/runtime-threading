[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     Distributor

# Distributor

The Distributor class is used for processing a no. of items on multiple consumers simultaneously.
The items aren't divided amongst the consumers, but duplicated thus enabling multiple consumers to process the same work.

### Example

```python
from runtime.threading import parallel

items = [ i for i in range(100)]

distributor = parallel.distribute(items)

consumers = [
     distributor.take()
     for _ in range(5)
]

task = distributor.start()

comsumed = [
     list(consumer)
     for consumer in consumers
]

for result in comsumed:
     assert result == items
```

## Constructors

### \_\_init\_\_(items: _Iterable[T]_)

Creates a new `Distributor` instance over the specified iterable.

- items `Iterable[T]`: The items to distribute.

## Functions start(interrupt: _Interrupt | None_ = _None_) -> _Task[None]_

Seals distributor and begins distributing. Returns a task which can be used to await the operation.

- interrupt `Interrupt | None` = An external interrupt used to stop the distribution. Defaults to `None`.

## take() -> _PIterable[T]_

Adds a consumer to the distributor instance. Note that any work already done by other consumers, will be lost at this point, so it's better to add all consumers before adding any work.