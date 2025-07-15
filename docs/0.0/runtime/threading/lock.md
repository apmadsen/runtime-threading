[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    Lock

# Lock : [LockBase](lock_base.md)

The `Lock` class limits concurrent access to objects by only allowing one single thread to acquire and hold it at any given time.

### Example

```python
from runtime.threading import Event, Lock
from runtime.threading.tasks import Task

event = Event()
lock = Lock()
data: dict[str, int] = { "i": 0 }

def fn(task: Task[int], signal: Event) -> int:
    signal.wait()
    with lock:
        data["i"] += 1
        return data["i"]

tasks = [ Task.run(fn, event) for x in range(5) ]

event.signal()

Task.wait_all(tasks)

result = sum( task.result for task in tasks )

assert result == sum(range(5+1))
```

### Constructor arguments

- reentrant `bool`: Specifies whether or not lock is reentrant (i.e. the same thread can acquire it several times at once).
