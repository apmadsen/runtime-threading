[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    InterruptSignal

# InterruptSignal

The `InterruptSignal` class is used to interrupt tasks asynchronously by signaling an underlying `Interrupt` instance.

## Constructors

### __init__()

Creates a new `InterruptSignal`.

### __init__(*linked_interrupts: _Interrupt_)

Creates a new `InterruptSignal` linked to one or more other interrupts.

*linked_interrupts `Interrupt`: One or more interrupts.

## Properties

### interrupt -> _Interrupt_

The associated `Interrupt` which will be signaled by calling `signal()` on this instance.

## Functions

### signal() -> _None_

Signals associated Interrupt.