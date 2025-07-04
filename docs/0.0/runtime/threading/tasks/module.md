[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    tasks

# runtime.threading.tasks module

## Modules

### [schedulers](schedulers/module.md)

## Variables

- DEFAULT_PARALLELISM `int`: The default parallelism. Defaults to `min(4, max(2, cpu_count())).`
- TASK_SUSPEND_AFTER `float`: The no. of seconds before suspending a task awaiting a lock or event. Defaults to `0.1`
- TASK_KEEP_ALIVE `float`: The no. of seconds background threads are kept alive by task schedulers before being reclaimed. Defaults to `0.1`
- POLL_INTERVAL `float`: The polling interval of events. Defaults to `0.1`

## Classes

### [AggregateException](aggregate_exception.md)
### [AwaitedTaskInterruptedError](awaited_task_interrupted_error.md)
### [ContinuationOptions](continuation_options.md)
### [ContinuationProto](continuation_proto.md)
### [Task](task.md)
### [TaskAlreadyRunningError](task_already_running_error.md)
### [TaskAlreadyScheduledError](task_already_scheduled_error.md)
### [TaskCompletedError](task_completed_error.md)
### [TaskException](task_exception.md)
### [TaskNotScheduledError](task_not_scheduled_error.md)
### [TaskProto](task_proto.md)
### [TaskState](task_state.md)

