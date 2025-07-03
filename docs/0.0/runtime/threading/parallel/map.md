[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     map

# map(items: _Iterable[Tin]_, /, task_name: _str | None_ = _None_, parallelism: _int | None_ = _None_, interrupt: _Interrupt | None_ = _None_, scheduler: _TaskScheduler | None_ = _None_) -> _MapProto[Tin]_

The `map` function inititates a parallel mapping process of multiple items and returns a `MapProto` wrapper.

### Example

```python
from typing import Iterable
from runtime.threading.tasks import Task
from runtime.threading import parallel

def fn(task: Task[Iterable[int]], s: int) -> Iterable[int]:
     yield s * 2

items = [ i for i in range(100)]
t1 = parallel.map(items, parallelism=5).do(fn)

result = sum(item for item in t1)

facit = sum(map(lambda x: x*2, items))
assert facit == result
```

## Arguments

- items `Iterable[Tin]`: The items to be processed.
- task_name `str | None`: The task name prefix. Defaults to `None`.
- parallelism `int | None` = The no. of parallel tasks to use. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel operation. Defaults to `None`.
- scheduler `TaskScheduler | None` = The task scheduler onto which tasks are sceduled. Defaults to `None`.