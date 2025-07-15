[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    InterruptSignal

# InterruptSignal

The `InterruptSignal` class is used to interrupt tasks asynchronously by signaling an underlying `Interrupt` instance.

### Example

```python
from runtime.threading import InterruptSignal, signal_after
from runtime.threading.tasks import Task

def fn(task: Task[None]):
    while True:
        task.interrupt.raise_if_signaled()
        ...

signal = InterruptSignal()
task = Task.create(interrupt = signal.interrupt).run(fn)
signal_after(signal, 0.1)
task.wait()

assert task.is_interrupted
```

## Constructors

### \_\_init\_\_()

Creates a new `InterruptSignal`.

### \_\_init\_\_(*linked_interrupts: _[Interrupt](interrupt.md)_)

Creates a new `InterruptSignal` linked to one or more other interrupts.

*linked_interrupts `Interrupt`: One or more interrupts.

## Properties

### interrupt -> _[Interrupt](interrupt.md)_

The associated `Interrupt` which will be signaled by calling `signal()` on this instance.

## Functions

### signal() -> _None_

Signals associated Interrupt.