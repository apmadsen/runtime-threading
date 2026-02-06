[Documentation](../../../../documentation.md) >
 [v0.0](../../../version.md) >
  [runtime](../../module.md) >
   [threading](../module.md) >
    [tasks](module.md) >
     TaskState

# TaskState : IntEnum

The `TaskState` enum describes the different states of a task.

### Members

- NOTSTARTED `0`: The initial task state where task may be scheduled on any scheduler.
- SCHEDULED `1`: The state of a task that's been scheduled.
- RUNNING `2`: The state of a running task.
- COMPLETED `3`: The state of a task that's run to completion without errors.
- INTERRUPTED `4`: The state of a task that was interrupted.
- FAILED `5`: The state of a task that is failed.