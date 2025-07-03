[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     ProducerConsumerQueue

# ProducerConsumerQueue

The `ProducerConsumerQueue` class is an implemention of the producer/consumer pattern,providing a queue on which work can be added and consumed asynchronously on different threads.

The workflow is as follows: The producer thread is responsible for putting items into the queue, and subsequently calline `complete()` when done, while the consumer merely
consumes the items by either calling `try_take()` repeatedly or iterating over an iterator created by calling `get_iterator()`. Due to the asynchronous nature of the queue, multiple iterators can be used simultaneously to parallelise consumption.

### Example

```python
from runtime.threading.parallel import ProducerConsumerQueue
from runtime.threading.tasks import Task

def fn_produce(task: Task[None], queue: ProducerConsumerQueue[int], n: int) -> None:
        try:
            for i in range(n):
                queue.put(i)
            queue.complete()
        except Exception as ex:
            queue.fail(ex)

def fn_consume(task: Task[list[int]], queue: ProducerConsumerQueue[int]) -> list[int]:
     return [ i for i in queue.get_iterator() ]

queue = ProducerConsumerQueue[int]()
task_producer = Task.run(fn_produce, queue, 5)
task_consumer = Task.run(fn_consume, queue)

assert task_consumer.result == list(range(5))
```

## Constructors

### \_\_init\_\_()

Creates a new empty `ProducerConsumerQueue`.

### \_\_init\_\_(data: _Iterable[T])

Creates a new `ProducerConsumerQueue` with existing work.

## Properties

### is_complete -> _bool_

Indicates if the queue is complete.

### is_failed -> _bool_

Indicates if the queue is failed.

### is_async -> _bool_

Indicates if the queue is consuming from another `ProducerConsumerQueue`.

### wait_event -> _Event_

The internal event, signaled when items are added or when `complete()`, `fail()` or `fail_if_not_complete()` is called.

## Functions

### put(item: _T_) -> _None_

Adds an item to the queue.

- item `T`: The item to be added.

### put_many(items: _Iterable[T]_) -> _None_

Adds multiple items to the queue.

- items `_Iterable[T]_`: The items to be added.

### take(timeout: _float | None_ = _0_, /, interrupt: _Interrupt | None_ = _None_) -> _T_

Tries to take an item from the queue. If a timeout is specified, call will block until an item can be produced or timeout is met. Will raise a `TimeoutError` exception if no item can be produced and timeout is not `None`.

- timeout `float`: The operation timeout. Defaults to `0`.
- interrupt `Interrupt | None`: An Interrupt for this specific call. Defaults to `None`.

### try_take(timeout: _float | None_ = _0_, /, interrupt: _Interrupt | None_ = _None_) -> _tuple[T | None, bool]_

Tries to take an item from the queue. If a timeout is specified, call will block until an item can be produced or timeout is met.

Returns a tuple consisting of the item produced and a boolean indicating success or not.

- timeout `float`: The operation timeout. Defaults to `0`.
- interrupt `Interrupt | None`: An Interrupt for this specific call. Defaults to `None`.

### complete() -> _None_

Marks the queue completed. The queue will not accept additional items afterwards.

### fail(error: _Exception_) -> _None_

Marks the queue failed with the specified exception. The queue will not accept additional items afterwards. Will raise a `QueueLinkedToAnotherQueueError` exception if queue is consuming from another `ProducerConsumerQueue`.

- error `Exception`: The exception that caused the process to fail.

### fail_if_not_complete(error: _Exception_) -> _None_

If not completed, marks the queue failed with the specified exception. The queue will not accept additional items afterwards. Will raise a `QueueLinkedToAnotherQueueError` exception if queue is consuming from another `ProducerConsumerQueue`.

- error `Exception`: The exception that caused the process to fail.

### get_iterator() -> _PIterable[T]_

Returns a `ProducerConsumerQueueIterator[T]` used for blocking interruptable iteration.