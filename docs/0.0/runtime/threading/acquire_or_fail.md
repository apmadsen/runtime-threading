[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    acquire_or_fail

# acquire_or_fail

The `acquire_or_fail` function tries to acquire a lock for a specific period of time(seconds), and, if unsuccessful, raises a specific exception afterwards.

### Arguments

- lock `Lock | Semaphore`: The lock to attempt acquiring.
- timeout `float`: The no. of seconds to wait.
- fail `() -> Exception`: A function which returns the exception which is to be raised.
- interrupt `Interrupt`: An external interrupt used to cancel operation.

### Example:

```python
from runtime.threading import Lock, acquire_or_fail
from runtime.threading.tasks import Task

lock = Lock()

with acquire_or_fail(lock, 1, lambda: Exception("Failed to acquire lock")):
    ...
```