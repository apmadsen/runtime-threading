[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    ContinueWhen

# ContinueWhen : IntEnum

The `ContinueWhen` enum is used to specify when a continuation is executed.

### Members

- ANY `1`: The continuation should executed when any of the awaited events are signaled.
- ALL `2`: The continuation should executed when all of the awaited events are signaled.