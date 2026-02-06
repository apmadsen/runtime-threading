[Documentation](../../../documentation.md) >
 [v0.0](../../version.md) >
  [runtime](../module.md) >
   [threading](module.md) >
    InterruptException

# InterruptException : [ThreadingException](threading_exception.md)

The `InterruptException` exception is raised whenever raise_if_signaled() is called on a signaled `Interrupt`.

A single exception is created when signaling an interrupt, and used whenever `raise_if_signaled()` is called.

## Properties

### interrupt -> _Interrupt_

The Interrupt associated with the exception.