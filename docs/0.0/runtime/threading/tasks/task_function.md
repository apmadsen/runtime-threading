[Documentation](../../../../documentation.md) >
 [v0.0](../../../version.md) >
  [runtime](../../module.md) >
   [threading](../module.md) >
    [tasks](module.md) >
     task

# task(fn: Callable[P, R]) -> Callable[P, [Task](task.md)[R]]

The `task` decorator wraps a function inside a task.

### Arguments

- fn `Callable[P, R]`: The function which is wrapped.

### Example

```python
from runtime.threading.tasks import task

@task
def sync_function(x: int) -> int:
     return x * 2

x = sync_function(2) # -> Task[int]

```

