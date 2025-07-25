[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     for_each

# for_each(items: _Iterable[T]_, /, task_name: _str | None_ = _None_, parallelism: _int | None_ = _None_, interrupt: _[Interrupt](../interrupt.md) | None_ = _None_, scheduler: _[TaskScheduler](../tasks/schedulers/task_scheduler.md) | None_ = _None_) -> _[ForEachProto](for_each_proto.md)[T]_

The `for_each` function inititates a parallel process of multiple items and returns a `ForEachProto` wrapper.

### Example

```python
from runtime.threading.tasks import Task, ContinuationOptions
from runtime.threading import parallel

queue = parallel.ProducerConsumerQueue[int]()

def fn(task: Task[None], s: int) -> None:
     queue.put(s * 2)

def fn_done(task: Task[None], preceding_task: Task[None]) -> None:
     queue.complete()

items = [ i for i in range(100)]
task1 = parallel.for_each(items, parallelism=5).do(fn)
task1.continue_with(ContinuationOptions.DEFAULT, fn_done)

result = sum(item for item in queue.get_iterator())

facit = sum(map(lambda x: x*2, items))
assert facit == result
```

## Arguments

- items `Iterable[T]`: The items to be processed.
- task_name `str | None`: The task name prefix. Defaults to `None`.
- parallelism `int | None` = The no. of parallel tasks to use. Defaults to `None`.
- interrupt `Interrupt | None` = An external interrupt used to cancel operation. Defaults to `None`.
- scheduler `TaskScheduler | None` = The task scheduler onto which tasks are sceduled. Defaults to `None`.