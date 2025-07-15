[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     [pipeline](/docs/0.0/runtime/threading/parallel/module.md) >
      NullPFn

# NullPFn : [PFn](p_fn.md)[Any, Any]

The `NullPFn` class is an extension of the base `PFn` class that simply just relays any work items to the next `PFn` in the pipeline. It's ideal for creating a pipeline which should fork its work.