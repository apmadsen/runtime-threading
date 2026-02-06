[Documentation](../../../../documentation.md) >
 [v0.0](../../../version.md) >
  [runtime](../../module.md) >
   [threading](../module.md) >
    [tasks](module.md) >
     ContinuationOptions

# ContinuationOptions : IntFlag

The `ContinuationOptions` enum is used to specify when and how a continuation is executed.

### Members

- INLINE `1`: The continuation task should be run inline (in the same thread) of the preceding task.
- ON_COMPLETED_SUCCESSFULLY `2`: The continuation should only be run when preceding task/tasks complete successfully.
- ON_FAILED `8`: The continuation should only be run when preceding task/tasks fails.
- ON_INTERRUPTED `16`: The continuation should only be run when preceding task/tasks complete successfully.
- DEFAULT `27`: A combination of all of the above.