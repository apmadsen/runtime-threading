[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     DistributionAlreadyStartedError

# DistributionAlreadyStartedError : Exception

The `DistributionAlreadyStartedError` exception is raised when a `Distributor` instance is requested to start more than once or when `take()` is called after being started.