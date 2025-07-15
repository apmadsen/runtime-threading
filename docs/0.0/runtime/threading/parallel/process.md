[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     process

# process(items: _Iterable[Tin]_, /, task_name: _str | None_ = _None_, parallelism: _int | None_ = _None_, interrupt: _[Interrupt](../interrupt.md) | None_ = _None_, scheduler: _[TaskScheduler](../tasks/schedulers/task_scheduler.md) | None_ = _None_) -> _[ProcessProto](process_proto.md)[Tin]_

The `process` function inititates a parallel process of multiple items and returns a `ProcessProto` wrapper.

### Example

```python
from typing import Iterable
from runtime.threading.tasks import Task
from runtime.threading import parallel

def fn_process(task: Task[Iterable[float]], item: int) -> Iterable[float]:
     yield 2 * item

items = [ i for i in range(1000) ]
facit = sorted(list(map(lambda x: 2 * x, items)))

output = parallel.process(items, parallelism = 5).do(fn_process)
result = sorted([ item for item in output ])

assert len(result) == len(items)
assert facit == result
```

## Arguments

- items `Iterable[Tin]`: The items to be processed.
- task_name `str | None`: The task name prefix. Defaults to `None`.
- parallelism `int | None` = The no. of parallel tasks to use. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel operation. Defaults to `None`.
- scheduler `TaskScheduler | None` = The task scheduler onto which tasks are sceduled. Defaults to `None`.