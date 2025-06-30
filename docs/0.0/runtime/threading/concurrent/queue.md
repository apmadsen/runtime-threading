[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [concurrent](/docs/0.0/runtime/threading/concurrent/module.md) >
     Queue

# Queue class : Iterable[T]

The Queue class is a thread-safe doubly linked FIFO queue.

## Static functions

### from_items(items: _Iterable[Tinput]_) -> _Queue[Tinput]_

Creates a new queue with preexisting items in it.

## Functions

### enqueue(self, item: _T_) -> _None_

Adds an item to the end of the queue.

### requeue(self, item: _T_) -> _None_

Adds an item to the beginning of the queue. This is used in cases when a consumer is unsuccessful processing an item, and that item should be processed asap by another.

### try_dequeue(self, timeout: _float | None_ = _None_, interrupt: _Interrupt | None_ = _None_) -> _tuple[T | None, bool]_

Tries to dequeue an item. If queue is empty or a timeout occurs, a default value or 'None, False' is returned.

### dequeue(self, timeout: _float | None_ = _None_, interrupt: _Interrupt | None_ = _None_) -> _tuple[T | None, bool]_

Dequeues an item. If queue is empty, operation waits for an item to be added.

## Example:

```python
from runtime.threading.concurrent import Queue

queue = Queue[str]()
queue.enqueue("this")
queue.enqueue("is")
queue.enqueue("a")
queue.enqueue("queue")
text = " ".join(queue) # -> 'this is a queue'
result, success = queue.try_dequeue() # -> None, False
```