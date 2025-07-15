[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     background

# background(*, task_name: _str | None_ = _None_, parallelism: _int | None_ = _None_, interrupt: _[Interrupt](../interrupt.md) | None_ = _None_, scheduler: _[TaskScheduler](../tasks/schedulers/task_scheduler.md)| None_ = _None_) -> _[BackgroundProto](background_proto.md)_

The `background` function inititates a parallel process of multiple items and returns a `BackgroundProto` wrapper.

### Example

```python
from runtime.threading.tasks import Task
from runtime.threading import parallel

queue = parallel.ProducerConsumerQueue[int]()
items = [ i for i in range(100) ]
facit = sum(map(lambda x: x*2, items))

def fn(task: Task[None], items: list[int]) -> None:
     for item in items:
          queue.put(item * 2)
     queue.complete()

parallel.background(parallelism=5).do(fn, items)

result = sum(item for item in queue.get_iterator())

assert facit == result
```

## Arguments

- task_name `str | None`: The task name prefix. Defaults to `None`.
- parallelism `int | None` = The no. of parallel tasks to use. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel operation. Defaults to `None`.
- scheduler `TaskScheduler | None` = The task scheduler onto which tasks are sceduled. Defaults to `None`.