[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     [pipeline](/docs/0.0/runtime/threading/parallel/module.md) >
      PFork

# PFork[Tin, Tout] : [PFn](p_fn.md)[Tin, Tout]

The `PFork` class is an extension of the base `PFn` class which forks out the same work items to a number of parallel functions simultaneously.

## Constructors

### \_\_init\_\_(fns: _Sequence[[PFn](p_fn.md)[Tin, Tout]]_)

Creates a new parallel forked function which returns the combined output of all inner functions.

- fns `Sequence[PFn[Tin, Tout]]`: The fork functions to parallelize.