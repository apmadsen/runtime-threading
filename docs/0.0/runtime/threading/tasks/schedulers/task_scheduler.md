[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [tasks](/docs/0.0/runtime/threading/tasks/module.md) >
     [schedulers](/docs/0.0/runtime/threading/tasks/module.md) >
      TaskScheduler

# TaskScheduler

The TaskScheduler class is the base task scheduler class responsible for managing the threads used by all derived schedulers.

## Properties

### synchronization_lock -> _threading.Lock_

The internal synchronization lock.

### is_closed -> _bool_

Abstract. Indicates if the scheduler has been closed.

### finalized -> _bool_

Indicates if object has been finalized or not.

### finalizing -> _bool_

Indicates if object is in the process of finalizing or not.

## Static functions

### default() -> _TaskScheduler_

Returns the default task scheduler (a ConcurrentTaskScheduler instance).

### current() -> _TaskScheduler_

Returns the task scheduler of the currently running task, or the default task scheduler if not called from within a running task.

### current_task() -> _[Task](../task.md)[Any] | None_

Returns the currently running task, if called from within one.

## Functions

### queue(task: _[Task](../task.md)[Any]_) -> _None_

Abstract. Queues the specified task.

- task `Task[Any]`: The task to queue.

### prioritise(task: _[Task](../task.md)[Any]_) -> _None_

Abstract. Runs the task inline of another. For internal use.

- task `Task[Any]`: The task to run.

### suspend() -> _ContextManager[Any]_

Abstract. Suspends the current task, ie. when waiting on an event. For internal use.