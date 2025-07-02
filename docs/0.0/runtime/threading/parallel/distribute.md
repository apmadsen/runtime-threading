[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     distribute

# distribute

The `distribute` function creates a `Distributor` instance which is used to distribute a sequence of items into several consumers.

- items `Iterable[T]`: The items to distribute.

### Example

```python
from random import randint
from runtime.threading import parallel

items = [ randint(0,100000) for _ in range(100)]

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