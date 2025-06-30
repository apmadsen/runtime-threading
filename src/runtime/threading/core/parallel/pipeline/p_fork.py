from math import ceil
from typing import TypeVar, Sequence, MutableSequence, Iterable, Any, cast

from runtime.threading.core.parallel.pipeline.p_iterable import PIterable
from runtime.threading.core.parallel.pipeline.p_context import PContext
from runtime.threading.core.parallel.pipeline.p_fn import PFn
from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.interrupt_signal import InterruptSignal
from runtime.threading.core.interrupt_exception import InterruptException

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")

class PFork(PFn[Tin, Tout]):
    """The PFork class is an extension of the base PFn class which forks out the same work items to a number
    of parallel functions simultaneously.
    """
    __slots__ = ["__fns", "__tasks", "__queue_out", "__queues"]

    def __init__(self, fns: Sequence[PFn[Tin, Tout]]):
        """Creates a new parallel forked function.

        Args:
            fns (Sequence[PFn[Tin, Tout]]): The fork functions to parallelize
        """

        super().__init__(None, 1.0) # pyright: ignore[reportCallIssue, reportArgumentType]
        self.__fns = fns
        self.__tasks: MutableSequence[Task[Any]] = []


    def __call__(self, items: PIterable[Tin] | Iterable[Tin]) -> PIterable[Tout]:
        if self._parent:
            items = self._parent(items)
        elif not isinstance(items, PIterable):
            items = ProducerConsumerQueue[Tin](items).get_iterator()
        else:
            pass

        self.__queues = [ (fn, ProducerConsumerQueue[Tin]()) for fn in self.__fns ]
        self.__queue_out = ProducerConsumerQueue[Tout]()

        pc = PContext.current()
        parallelism = min(len(self.__fns), self._parallelism if isinstance(self._parallelism, int) else ceil(self._parallelism * pc.max_parallelism))
        signal = InterruptSignal(pc.interrupt)

        for fn, queue in self.__queues:
            self.__tasks.append(fn._output(queue.get_iterator(), self.__queue_out))

        def fork_fn(task: Task[None], items: PIterable[Tin]) -> None:
            task.interrupt.raise_if_signaled()
            for item in items:
                task.interrupt.raise_if_signaled()
                for _, queue in self.__queues:
                    queue.put(item)


        def succeeded(task: Task[Any], tasks: Iterable[Task[Any]]):
            for _, queue in self.__queues:
                queue.complete()

        def interrupted(task: Task[Any], tasks: Iterable[Task[Any]]): # pragma: no cover
            signal.signal()
            for _, queue in self.__queues:
                queue.fail(InterruptException(task.interrupt))

        def failed(task: Task[Any], tasks: Iterable[Task[Any]]):
            signal.signal()
            exception = AggregateException(tuple(cast(Exception, task.exception) for task in tasks if task.is_failed ))

            for _, queue in self.__queues:
                queue.fail_if_not_complete(exception)

            self.__queue_out.fail(exception)

        def complete_queue(task: Task[Any], tasks: Iterable[Task[Any]]):
            self.__queue_out.complete()



        tasks = [
            Task.create(
                scheduler = pc.scheduler,
                interrupt = signal.interrupt
            ).run(
                fork_fn,
                items,
            ) for _ in range(parallelism)
        ]

        t_succeeded = Task.with_all(tasks, options=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY).run(succeeded)
        t_failed = Task.with_any(tasks, options=ContinuationOptions.ON_FAILED | ContinuationOptions.INLINE).run(failed)
        t_interrupted = Task.with_any(tasks, options=ContinuationOptions.ON_INTERRUPTED | ContinuationOptions.INLINE).run(interrupted)

        Task.with_all([ *self.__tasks, *tasks, t_interrupted, t_failed, t_succeeded ], options=ContinuationOptions.DEFAULT).run(complete_queue)

        return self.__queue_out.get_iterator()