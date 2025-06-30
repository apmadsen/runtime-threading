[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [tasks](/docs/0.0/runtime/threading/tasks/module.md) >
     AwaitedTaskInterruptedError

# AwaitedTaskInterruptedError : TaskException

The `AwaitedTaskInterruptedError` exception is raised when one or more awaited tasks were interrupted (applies to `Task.wait_any()` and `Task.wait_all()`).