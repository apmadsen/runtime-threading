[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    Interrupt

# Interrupt

The `Interrupt` class is used for asynchronous task interruption. The Interrupt instance can be passed around between tasks and used to poll for interruption, while the `InterruptSignal` is used for signaling the `Interrupt`.

## Properties

### is_signaled -> _bool_

Indicates if Interrupt has been signaled.

### signal_id -> _int | None_

The id of the signal (if signaled).

### wait_event -> _Event_

The internal event which handles signaling.

## Static functions

### none() -> _Interrupt_

Returns a default interrupt which will never be signaled.

## Functions

### propagates_to(interrupt: _Interrupt_) -> _bool_

Indicates if the interrupt instance is linked to an other interrupt. Note: This information is not available after interrupt has been signaled.

- interrupt `Interrupt`: The other interrupt to check for propagation.

### raise_if_signaled() -> _None_

Raises an InterruptException if signaled.

### wait(timeout: _float | None_, interrupt: _Interrupt | None_) -> _bool_

Waits for signal. Same as `wait_handle.wait()`.

- timeout `float | None`: The no. of seconds to wait before returning `False`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.

Returns `True` if signaled, `False` otherwise.