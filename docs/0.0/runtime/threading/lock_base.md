[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    LockBase

# LockBase

The `LockBase` class is the base class of locks (`Lock` and `Semaphore`).

## Constructors

### \_\_init\_\_(lock: _RLock | TLock | Semaphore_)

- lock `RLock | TLock | Semaphore`: A builtin mutex from the threading module.

## Functions

### acquire(timeout: _float_, interrupt: _[Interrupt](interrupt.md) | None_ = _None_) -> _bool_

Acquires the lock.

- timeout `float`: The no. of seconds to wait
- interrupt `Interrupt | None`: An external interrupt used to cancel operation. Defaults to `None`

### release() -> _None_

Releases the lock.