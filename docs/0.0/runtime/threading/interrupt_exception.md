[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    InterruptException

# InterruptException : [ThreadingException](threading_exception.md)

The `InterruptException` exception is raised whenever raise_if_signaled() is called on a signaled `Interrupt`.

A single exception is created when signaling an interrupt, and used whenever `raise_if_signaled()` is called.

## Properties

### interrupt -> _Interrupt_

The Interrupt associated with the exception.