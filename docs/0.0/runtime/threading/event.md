[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    Event

# Event

The `Event` class is used for synchronization between threads.

## Constructors

### __init__()

Creates an event.

### __init__(internal_event: _threading.Event_)

Creates an event from an existing builtin event.

- internal_event `threading.Event`: The preexisting builtin event instance.

## Properties

### is_signaled -> _bool_

Indicates if the event is signaled or not.

### purpose -> _Purpose_

Returns the event purpose (for testing).

## Functions

### signal() -> _None_

Signals the event.

### clear() -> _None_

Clears the event flag rendering it not signaled.

### wait(timeout: _float | None_, interrupt: _Interrupt | None_) -> _bool_

Waits for the event to be signaled.

- timeout `float | None`: The no. of seconds to wait before returning `False`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.

Returns `True` if signaled, `False` otherwise.

## Static functions

### wait_any(events: _Sequence[Event]_, timeout: _float | None_, interrupt: _Interrupt | None_ = _None_) -> _bool_

Waits for any of the specified events to be signaled.

- events `Sequence[Event]`: The awaited events.
- timeout `float | None`: The no. of seconds to wait before returning `False`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.

Returns True if any of the events were signaled. Otherwise False.


### wait_all(events: _Sequence[Event]_, timeout: _float | None_, interrupt: _Interrupt | None_ = _None_) -> _bool_

Waits for all of the specified events to be signaled.

- events `Sequence[Event]`: The awaited events.
- timeout `float | None`: The no. of seconds to wait before returning `False`.
- interrupt `Interrupt | None`: An external interrupt used to cancel operation.

Returns True if all of the events were signaled. Otherwise False.