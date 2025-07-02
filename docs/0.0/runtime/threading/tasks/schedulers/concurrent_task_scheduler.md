[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [tasks](/docs/0.0/runtime/threading/tasks/module.md) >
     [schedulers](/docs/0.0/runtime/threading/tasks/module.md) >
      ConcurrentTaskScheduler

# ConcurrentTaskScheduler : TaskScheduler

The `ConcurrentTaskScheduler` class is a task scheduler for concurrent workloads, with a predefined max degree of parallelism.

### Example

```python
from runtime.threading.tasks import Task
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler

def fn(task: Task[str]) -> str:
      return "abc"

with ConcurrentTaskScheduler(8) as scheduler:
      task = Task.create(scheduler = scheduler).run(fn)

result = task.result # -> "abc"

assert result == "abc"
```

## Constructors

### \_\_init\_\_(max_parallelism: _int_ = _DEFAULT_PARALLELISM_, keep_alive: _float_ = _TASK_KEEP_ALIVE_)

Creates a new ConcurrentTaskScheduler instance.

- max_parallelism `int`: The max degree of parallelism (i.e. active threads). Defaults to the no. of CPUs.
- keep_alive `float`: The no. of seconds to keep threads alive, before reclaiming them. Defaults to 0.1.

## Properties

### is_closed -> _bool_

Returns True if scheduler is closed.

### max_parallelism -> _int_

The max degree of parallelism i.e. no. active tasks.

### keep_alive -> _float_

The no. of seconds to keep threads alive, before reclaiming them.

### allocated_threads -> _int_

The no. of currently allocated threads. This does not include suspended threads.

### active_threads -> _int_

The no. of currently active threads.

### suspended_threads -> _int_

The no. of currently suspended threads.

## Functions

### queue(task: _Task[Any]_) -> _None_

Queues the task. Should not be called directly - use `Task.schedule(scheduler)` instead...

#### prioritise(self, task: _T_ask[Any]_) -> _None_

Runs the task inline of another. For internal use.

- task `Task[Any]`: The task to run.

### suspend() -> _ContextManager[Any]_

Suspends the current task, ie. when waiting on an event. For internal use.

### close() -> _None_

Closes the scheduler and waits for any scheduled tasks to finish.