from math import ceil
from typing import TypeVar, Sequence, MutableSequence, Iterable, Any, cast

from runtime.threading.core.parallel.p_iterable import PIterable
from runtime.threading.core.parallel.parallel_context import ParallelContext
from runtime.threading.core.parallel.pipeline.p_fn import PFn
from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.tasks.task_interrupt_exception import TaskInterruptException

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")

class PFork(PFn[Tin, Tout]):
    __slots__ = ["__fns", "__tasks", "__queue_out", "__queues"]

    # @overload
    def __init__(self, fns: Sequence[PFn[Tin, Tout]]):
        """Creates a new parallel forked function

        Args:
            fns (Sequence[PFn[Tin, Tout]]): The fork functions to parallelize
        """
    #     ...
    # @overload
    # def __init__(self, fns: Sequence[PFn[Tin, Tout]], parallelism: int):
    #     """Creates a new parallel forked function

    #     Args:
    #         fns (Sequence[PFn[Tin, Tout]]): The fork functions to parallelize
    #         parallelism (int): An int between 1 and 32 representing the max no. of parallel threads.
    #     """
    #     ...
    # @overload
    # def __init__(self, fns: Sequence[PFn[Tin, Tout]], parallelism: float):
    #     """Creates a new parallel forked function

    #     Args:
    #         fns (Sequence[PFn[Tin, Tout]]): The fork functions to parallelize
    #         parallelism (float): A float between 0.0 and 1.0 representing the no. of parallel threads relative to the max parallelism of the current PContext
    #     """
    #     ...
    # def __init__(self, fns: Sequence[PFn[Tin, Tout]], parallelism: int | float = 2):
        super().__init__(None, 1.0) # type: ignore
        self.__fns = fns
        self.__tasks: MutableSequence[Task[Any]] = []
        # self._parallelism = parallelism

    def __call__(self, items: PIterable[Tin] | Iterable[Tin]) -> PIterable[Tout]:
        if self._parent:
            items = self._parent(items)
        elif not isinstance(items, PIterable):
            items = ProducerConsumerQueue[Tin](items).get_iterator()

        self.__queues = [ (fn, ProducerConsumerQueue[Tin]()) for fn in self.__fns ]
        self.__queue_out = ProducerConsumerQueue[Tout]()

        for fn, queue in self.__queues:
            self.__tasks.append(fn._output(queue.get_iterator(), self.__queue_out))

        def fork_fn(task: Task[None], items: PIterable[Tin]) -> None:
            for item in items:
                for _, queue in self.__queues:
                    queue.put(item)


        def complete_queues(task: Task[Any], tasks: Iterable[Task[Any]]):
            for _, queue in self.__queues:
                queue.complete()

        def cancel_queues(task: Task[Any], tasks: Iterable[Task[Any]]):
            for _, queue in self.__queues:
                queue.fail(TaskInterruptException(task.interrupt))

        def fail_queues(task: Task[Any], tasks: Iterable[Task[Any]]):
            exceptions: MutableSequence[Exception] = []
            for failed_task in [ task for task in tasks if task.is_failed ]:
                exception = cast(Exception, failed_task.exception)
                if isinstance(exception, AggregateException):
                    exception = exception.flatten()

                exceptions.append(exception)

            ex = AggregateException(exceptions).flatten()
            for _, queue in self.__queues:
                queue.fail_if_not_complete(ex)

            self.__queue_out.fail(ex)



        def complete_queue(task: Task[Any], tasks: Iterable[Task[Any]]):
            self.__queue_out.complete()




        pc = ParallelContext.current()
        parallelism = self._parallelism if isinstance(self._parallelism, int) else ceil(self._parallelism * pc.max_parallelism)
        tasks = [
            Task.create(
                scheduler = pc.scheduler,
                interrupt = pc.interrupt
            ).run(
                fork_fn,
                items,
            ) for _ in range(parallelism)
        ]

        t_complete = Task.with_all(tasks, options=ContinuationOptions.DEFAULT).then(complete_queues)
        t_fail = Task.with_any(tasks, options=ContinuationOptions.ON_FAILED | ContinuationOptions.INLINE).then(fail_queues)
        t_cancel = Task.with_any(tasks, options=ContinuationOptions.ON_CANCELED | ContinuationOptions.INLINE).then(cancel_queues)

        Task.with_all([ *self.__tasks, *tasks, t_cancel, t_fail, t_complete ], options=ContinuationOptions.DEFAULT).then(complete_queue)

        return self.__queue_out.get_iterator()