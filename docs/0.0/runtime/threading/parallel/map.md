[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     map

# map(items: _Iterable[Tin]_, /, task_name: _str | None_ = _None_, parallelism: _int | None_ = _None_, interrupt: _[Interrupt](../interrupt.md) | None_ = _None_, scheduler: _[TaskScheduler](../tasks/schedulers/task_scheduler.md) | None_ = _None_) -> _[MapProto](map_proto.md)[Tin]_

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