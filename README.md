[![Test](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test.yml/badge.svg)](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test.yml)
[![Coverage](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test-coverage.yml/badge.svg)](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test-coverage.yml)
[![Stable Version](https://img.shields.io/pypi/v/runtime-threading?label=stable&sort=semver&color=blue)](https://github.com/apmadsen/runtime-threading/releases)
![Pre-release Version](https://img.shields.io/github/v/release/apmadsen/runtime-threading?label=pre-release&include_prereleases&sort=semver&color=blue)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runtime-threading)
[![PyPI Downloads](https://static.pepy.tech/badge/runtime-threading/week)](https://pepy.tech/projects/runtime-threading)

# Runtime Threading

A high-level task abstraction layer for Python — designed to make concurrency easier to reason about.

## 🚀 Why this exists

Concurrency in Python is powerful — but often difficult to structure:

- Threads, locks, and events quickly become hard to coordinate
- Async and threading models are not always intuitive to combine
- Simple tasks grow into complex orchestration problems

👉 This library focuses on one thing:
Making concurrent code **composable, predictable, and easier to work with**



## ✨ Features

- 🧵 Run background tasks and await completion or failure
- 🔗 Coordinate multiple tasks, locks, and events
- 📦 Built-in support for producer/consumer patterns
- ⚡ Simplified parallel operations like map and foreach
- 🔄 Continuation-based task chaining
- 🧠 Structured task orchestration



## 📦 Use cases

This library is useful when building:

- Data pipelines
- Background workers / job systems
- Concurrent processing workflows
- Event-driven systems
- Services that require coordination between multiple tasks

👉 Especially valuable when concurrency becomes more than just "run this in a thread".

## ⚖️ Trade-offs
| Focus ✅ | Not a goal ❌ |
|---|---|
|Task abstraction|Full async framework replacement|
|Simplicity|Handling every edge-case in concurrency|
|Composability|Low-level thread control|

👉 The goal is not to replace Python’s concurrency primitives —
but to make them easier to use correctly.

## ⚙️ Example

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