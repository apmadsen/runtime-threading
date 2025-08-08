[![Test](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test.yml/badge.svg)](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test.yml)
[![Coverage](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test-coverage.yml/badge.svg)](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test-coverage.yml)
[![Stable Version](https://img.shields.io/pypi/v/runtime-threading?label=stable&sort=semver&color=blue)](https://github.com/apmadsen/runtime-threading/releases)
![Pre-release Version](https://img.shields.io/github/v/release/apmadsen/runtime-threading?label=pre-release&include_prereleases&sort=semver&color=blue)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runtime-threading)
[![PyPI Downloads](https://static.pepy.tech/badge/runtime-threading/week)](https://pepy.tech/projects/runtime-threading)

# runtime-threading
This project provides a task based abstraction to threading.

## Example

```python
from runtime.threading import InterruptSignal, InterruptException
from runtime.threading.tasks import Task, ContinuationOptions

try:
     signal = InterruptSignal()
     i = 227
     m = 0.78

     def fn(task: Task[float], i: float, m: float) -> float:
          task.interrupt.raise_if_signaled()
          return i * m

     def fn_continue(task: Task[float], preceding_task: Task[float], m: float) -> float:
          return preceding_task.result * m

     task1 = Task.run(fn, i, m)
     task2 = task1.continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY, fn_continue, m)

     result1 = task1.result # -> 177.06
     result2 = task2.result # -> 138.1068

     task3 = Task.create(interrupt = signal.interrupt, lazy = True).plan(fn, task1.result, m)

     signal.signal()

     # task3 is run lazily when result property is accessed
     result3 = task3.result # TaskInterruptedException

except InterruptException:
     pass # won't happen since the interrupt is never signaled
```
## Full documentation

[Go to documentation](https://github.com/apmadsen/runtime-threading/blob/main/docs/documentation.md)