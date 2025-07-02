[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    signal_after

# signal_after

The `signal_after` function creates a task which signals an InterruptSignal instance after a certain  amount of time (seconds).

### Arguments

- signal `InterruptSignal`: The InterruptSignal to signal.
- time `float`: The no. of seconds to wait.

### Example:

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
```