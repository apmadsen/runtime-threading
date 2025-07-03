[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     distribute

# distribute(items: _Iterable[T]_) -> _Distributor[T]_

Creates a `Distributor` instance which is used to distribute a sequence of items into several consumers.

- items `Iterable[T]`: The items to distribute.

# distribute(items: _Iterable[T]_, scheduler: _TaskScheduler_) -> _Distributor[T]_

Creates a `Distributor` instance which is used to distribute a sequence of items into several consumers.

- items `Iterable[T]`: The items to distribute.
- scheduler `TaskScheduler`: The scheduler onto which tasks are scheduled.

### Example

```python
from runtime.threading import parallel

items = [ i for i in range(100) ]

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