[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    sleep

# sleep

The `sleep` function is directly linked to `terminate_event.wait` and should be used as a direct replacement for `time.sleep(x)` due to the fact that all awaitables in this package support task suspension, whereas the builtin do not.

Task suspension is a mechanism allowing task schedulers to suspend underlying threads thus enabling them to utilize more threads in total, and it means that awaiting locks, events, interrupts and tasks won't use up available threads in a scheduler.

### Arguments

- time `float`: A float specifying the no. of seconds
- interrupt `Interrupt | None`: An external interrupt. Defaults to `None`.