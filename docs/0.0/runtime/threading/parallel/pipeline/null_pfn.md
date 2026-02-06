[Documentation](../../../../../documentation.md) >
 [v0.0](../../../../version.md) >
  [runtime](../../../module.md) >
   [threading](../../module.md) >
    [parallel](../module.md) >
     [pipeline](module.md) >
      NullPFn

# NullPFn : [PFn](p_fn.md)[Any, Any]

The `NullPFn` class is an extension of the base `PFn` class that simply just relays any work items to the next `PFn` in the pipeline. It's ideal for creating a pipeline which should fork its work.