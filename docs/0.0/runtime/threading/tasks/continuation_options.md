[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [tasks](/docs/0.0/runtime/threading/tasks/module.md) >
     ContinuationOptions

# ContinuationOptions : IntFlag

The `ContinuationOptions` enum is used to specify when and how a continuation is executed.

### Members

- INLINE `1`: The continuation task should be run inline (in the same thread) of the preceding task.
- ON_COMPLETED_SUCCESSFULLY `2`: The continuation should only be run when preceding task/tasks complete successfully.
- ON_FAILED `8`: The continuation should only be run when preceding task/tasks fails.
- ON_INTERRUPTED `16`: The continuation should only be run when preceding task/tasks complete successfully.
- DEFAULT `27`: A combination of all of the above.