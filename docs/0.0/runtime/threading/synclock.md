[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    synclock

# synclock(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]

The `synclock` decorator applies lock synchronization to a range of functions or methods. Functions sharing the same synclock name, will share the same underlying lock.

### Arguments

- name `str`: The name of the range which shares the same lock.

### Example

```python
from runtime.threading import synclock

class AsyncTask:

    @synclock("group1")
    def sync_function1(self, x: int) -> int:
        return x * 2

    @synclock("group1")
    def sync_function2(self, x: int) -> int:
        return x * 2

    @synclock("group2")
    def sync_function3(self, x: int) -> int:
        return x * 2

```

# synclock(fn: Callable[P, R]) -> Callable[P, R]

The `synclock` decorator applies lock synchronization to a single function or method..

### Arguments

- fn `Callable[P, R]`: The function which is wrapped.

### Example

```python
from runtime.threading import synclock

class AsyncTask:

    @synclock
    def sync_function(self, x: int) -> int:
        return x * 2

```

