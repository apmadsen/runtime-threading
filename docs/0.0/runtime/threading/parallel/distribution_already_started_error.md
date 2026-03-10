[Documentation](../../../../documentation.md) >
 [v0.0](../../../version.md) >
  [runtime](../../module.md) >
   [threading](../module.md) >
    [parallel](module.md) >
     DistributionAlreadyStartedError

# DistributionAlreadyStartedError : [ParallelException](parallel_exception.md)

The `DistributionAlreadyStartedError` exception is raised when a `Distributor` instance is requested to start more than once or when `take()` is called after being started.