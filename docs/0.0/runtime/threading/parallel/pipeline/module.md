[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    [parallel](/docs/0.0/runtime/threading/parallel/module.md) >
     pipeline

# runtime.threading.parallel.pipeline module

## Classes

### [NullPFn](null_pfn.md)
### [PContext](p_context.md)
### [PFilter](p_filter.md)
### [PFn](p_fn.md)
### [PFork](p_fork.md)
### [PipelineException](pipeline_exception.md)
### [PIterable](p_iterable.md)
### [PIterator](p_iterator.md)

### Example:

```python
from runtime.threading.tasks import Task
from runtime.threading.tasks.schedulers import ConcurrentTaskScheduler
from runtime.threading.parallel.pipeline import PFn, PFilter, PContext

with ConcurrentTaskScheduler(4) as scheduler:
      with PContext(scheduler.max_parallelism, scheduler = scheduler) as ctx:

      def fn_filter_uneven(task: Task[Iterable[int|float]], item: int|float) -> bool:
            return item % 2 == 0

      def fn_multiply(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
            task.interrupt.raise_if_signaled()
            yield item * 1.5

      def fn_divide(task: Task[Iterable[int|float]], item: int|float) -> Iterable[float]:
            task.interrupt.raise_if_signaled()
            yield item / 2

      pipeline = (
        PFilter(fn_filter_uneven) # filters out all uneven numbers bringing the workload down from 1000 to 500 items
          | PFn(fn_multiply) # multiplies by 1.5
            | [
                PFn(fn_divide), # divides by 2
                PFn(fn_divide) # divides by 2
              ] # the fork multiplies the workload with the no. of functions in it bringing the workload up from 500 to 1000
      )

      o = 1000
      facit = [ ((i * 1.5) / 2) for i in range(o) if i % 2 == 0]
      result = list(pipeline(range(o))) # -> 1000 items

```