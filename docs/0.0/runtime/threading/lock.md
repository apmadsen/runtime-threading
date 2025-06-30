[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    Lock

# Lock : LockBase

The `Lock` class limits concurrent access to objects by only allowing one single thread to acquire and hold it at any given time.

### Constructor arguments

- reentrant `bool`: Specifies whether or not lock is reentrant (i.e. the same thread can acquire it several times at once).
