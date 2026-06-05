[![Test](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test.yml/badge.svg)](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test.yml)
[![Coverage](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test-coverage.yml/badge.svg)](https://github.com/apmadsen/runtime-threading/actions/workflows/python-test-coverage.yml)
[![Stable Version](https://img.shields.io/pypi/v/runtime-threading?label=stable&sort=semver&color=blue)](https://github.com/apmadsen/runtime-threading/releases)
![Pre-release Version](https://img.shields.io/github/v/release/apmadsen/runtime-threading?label=pre-release&include_prereleases&sort=semver&color=blue)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runtime-threading)
[![PyPI Downloads](https://static.pepy.tech/badge/runtime-threading/week)](https://pepy.tech/projects/runtime-threading)

# Runtime Threading

A high-level task abstraction layer for Python — designed to make concurrency easier to reason about and structure.

## 🚀 Why this exists

Concurrency in Python is powerful, but quickly becomes difficult to manage as systems grow:

- Coordination between tasks becomes complex
- Threads, locks, and events introduce implicit behavior
- Control flow becomes harder to follow
- Simple parallel work evolves into orchestration problems

👉 The core challenge is not execution — it's coordination.

This project introduces a **structured task abstraction** that makes concurrent systems easier to design, understand, and evolve.


## ✨ Features

- 🧵 High-level task abstraction over threading primitives
- 🔗 Coordination between tasks, locks, and events
- 📦 Built-in support for producer/consumer patterns
- ⚡ Simplified parallel operations
- 🔄 Continuation-based workflows
- 🧠 Structured task orchestration


## 📦 Use cases

This library is particularly useful when building:

- Data pipelines
- Background processing systems
- Job orchestration workflows
- Event-driven architectures
- Services with coordinated parallel workloads

👉 Especially valuable when concurrency becomes part of the system design — not just an implementation detail.


## 🧵 Core idea

Instead of working directly with low-level primitives such as threads or synchronization objects,
this library introduces a **Task abstraction** as the central unit of execution.

A task:

- Represents a complete unit of work
- Has a well-defined lifecycle
- Can be composed with other tasks
- Provides consistent handling of success and failure

👉 This enables reasoning about concurrency at a higher level.


## 🔄 Composability & orchestration

One of the key goals of this project is to make concurrent workflows composable:

- Multiple tasks can be coordinated as a group
- Execution flow can be expressed declaratively
- Dependencies between tasks become explicit

👉 This shifts concurrency from *control flow complexity* to *structured orchestration*.


## 📦 Producer / Consumer patterns

The library includes support for queue-based processing patterns:

- Decouples producers from consumers
- Enables scalable work distribution
- Simplifies pipeline-style architectures

👉 A common building block in data and backend systems.


## 🏗 Design philosophy

This project is built on a few key principles:

### 1. Abstraction over primitives
Low-level threading constructs are powerful but difficult to scale in complexity.

### 2. Composability over ad-hoc concurrency
Tasks should be easy to combine, coordinate, and reuse.

### 3. Predictability over flexibility
Clear execution flow is prioritized over complex edge-case handling.

### 4. Developer experience
Concurrency should be understandable — not something developers avoid.


## 🔗 What this enables

By introducing structured task orchestration, this library allows you to:

- Build clearer concurrent architectures
- Reduce coordination complexity
- Improve readability of parallel workflows
- Make systems easier to debug and maintain

👉 Particularly useful in systems where concurrency is a core concern.


## ⚖️ Trade-offs

| Focus ✅ | Not a goal ❌ |
|---------|--------------|
| Task abstraction | Full async framework replacement |
| Structured orchestration | Fine-grained thread control |
| Composability | Covering every concurrency edge case |

👉 The goal is not to replace Python’s concurrency model —
but to make it **more usable in real-world systems**.


## 🧠 Inspiration

Inspired by:

- Task-based programming models (e.g. C# Task Parallel Library)
- Real-world concurrency challenges in backend systems
- The need for more structured abstractions in Python


## 🎯 When to use

Use this library if you:

- Work with non-trivial concurrency
- Need to coordinate multiple operations
- Want clearer structure in parallel workflows
- Prefer higher-level abstractions over low-level control


## 🚫 When not to use

This library may not be necessary if:

- Your concurrency needs are very simple
- Direct use of threading or async is sufficient
- You require fine-grained control over execution primitives


## 🔗 Related projects

Part of a broader focus on:

- Runtime abstractions
- Clean architecture
- Developer tooling in Python

👉 https://github.com/apmadsen


## 🤝 Contributing

Feedback and contributions are welcome!

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