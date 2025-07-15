from __future__ import annotations
from typing import Iterable, Callable, Sequence, TypeVar, Generic, Any, overload, cast
from math import ceil
import collections.abc

from runtime.threading.core.tasks.task import Task
from runtime.threading.core.parallel.pipeline.pipeline_exception import PipelineException
from runtime.threading.core.parallel.process import process
from runtime.threading.core.parallel.producer_consumer_queue import ProducerConsumerQueue
from runtime.threading.core.parallel.pipeline.p_context import PContext
from runtime.threading.core.parallel.pipeline.p_iterable import PIterable

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")
Tnext = TypeVar("Tnext")

class PFn(Generic[Tin, Tout]):
    """The PFn class (short for Parallel Function) is the heart of the parallel pipelines. It uses
    parallel.process() internally to process the work it's given and gets its parameters from the
    PContext parallel context.
    """

    __slots__ = ["__fn", "_parent", "_parallelism"]

    @overload
    def __init__(self, fn: Callable[[Task[Iterable[Tout]], Tin], Iterable[Tout]]) -> None:
        """Creates a new parallel function.

        Args:
            fn (Callable[[Task[Iterable[Tout]], Tin], Iterable[Tout]): The function to parallelize
        """
        ...
    @overload
    def __init__(self, fn: Callable[[Task[Iterable[Tout]], Tin], Iterable[Tout]], parallelism: int) -> None:
        """Creates a new parallel function.

        Args:
            fn (Callable[[Task[Iterable[Tout]], Tin], Iterable[Tout]): The function to parallelize
            parallelism (int): An int between 1 and 32 representing the max no. of parallel threads.
        """
        ...
    @overload
    def __init__(self, fn: Callable[[Task[Iterable[Tout]], Tin], Iterable[Tout]], parallelism: float) -> None:
        """Creates a new parallel function.

        Args:
            fn (Callable[[Task[Iterable[Tout]], Tin], Iterable[Tout]): The function to parallelize
            parallelism (float): A float between 0.0 and 1.0 representing the no. of parallel threads relative to the max parallelism of the current PContext
        """
        ...
    def __init__(self, fn: Callable[[Task[Iterable[Tout]], Tin], Iterable[Tout]] | None, parallelism: int | float = 1.0):
        self._parent: PFn[Any, Tin] | None = None
        self.__fn = fn

        if isinstance(parallelism, float):
            if 1 >= parallelism > 0:
                self._parallelism = parallelism
            else:
                raise ValueError("Parallelism must be a float between 0.0 and 1.0") # pragma: no cover
        else:
            if 32 >= parallelism > 0:
                self._parallelism = parallelism
            else:
                raise ValueError("Parallelism must be an int between 1 and 32") # pragma: no cover

    def __call__(self, items: PIterable[Tin] | Iterable[Tin]) -> PIterable[Tout]:
        if not self.__fn:
            raise PipelineException("Parallel function is NULL") # pragma: no cover

        pc = PContext.current()
        output = process(
            self._parent(items) if self._parent else items,
            parallelism = self._parallelism if isinstance(self._parallelism, int) else ceil(self._parallelism * pc.max_parallelism),
            scheduler = pc.scheduler,
            interrupt = pc.interrupt
        ).do(
            self.__fn,
        )
        return output

    def _output(self, items: Iterable[Tin], output_queue: ProducerConsumerQueue[Tout]) -> Task[Any]:
        if not self.__fn:
            raise PipelineException("Parallel function is NULL") # pragma: no cover

        pc = PContext.current()
        return process(
            self._parent(items) if self._parent else items,
            parallelism = self._parallelism if isinstance(self._parallelism, int) else ceil(self._parallelism * pc.max_parallelism),
            scheduler = pc.scheduler,
            interrupt = pc.interrupt
        ).do(
            self.__fn,
            output_queue = output_queue,
        )

    def _convert_next(
        self,
        next: PFn[Tout, Tnext] | Sequence[PFn[Tout, Tnext]] | Callable[[Task[Iterable[Tout]], Tout], bool]
    ) -> PFn[Tout, Tnext]:
        if isinstance(next, collections.abc.Sequence):
            from runtime.threading.core.parallel.pipeline.p_fork import PFork
            next = PFork[Tout, Tnext](cast(Sequence[PFn[Tout, Tnext]], next))
        elif isinstance(next, Callable) and not isinstance(next, PFn): # pyright: ignore[reportUnnecessaryIsInstance]
            from runtime.threading.core.parallel.pipeline.p_filter import PFilter
            next = cast(PFn[Tout, Tnext], PFilter[Tout](next))

        return next

    @overload
    def __or__(self, next: PFn[Tout, Tnext]) -> PFn[Tin, Tnext]:
        ...
    @overload
    def __or__(self, next: Sequence[PFn[Tout, Tnext]]) -> PFn[Tin, Tnext]:
        ...
    @overload
    def __or__(self, next: Callable[[Task[Iterable[Tout]],Tout], bool]) -> PFn[Tin, Tout]:
        ...
    def __or__(
        self,
        next: PFn[Tout, Tnext] | Sequence[PFn[Tout, Tnext]] | Callable[[Task[Iterable[Tout]], Tout], bool]
    ) -> PFn[Tin, Tnext]:
        next = self._convert_next(next)
        next._parent = self
        return cast(PFn[Tin, Tnext], next)


class NullPFn(PFn[Any, Any]):
    """The NullPFn class is an extension of the base PFn class that simply just relays any work items to the next PFn in the pipeline.
    It's ideal for creating a pipeline which should fork its work.
    """
    def __init__(self):
        """Override standard PFn constructor"""
        pass

    @overload
    def __or__(self, next: PFn[Tin, Tout]) -> PFn[Tin, Tout]:
        ...
    @overload
    def __or__(self, next: Sequence[PFn[Tin, Tout]]) -> PFn[Tin, Tout]:
        ...
    @overload
    def __or__(self, next: Callable[[Task[Iterable[Tout]],Tout], bool]) -> PFn[Tout, Tout]:
        ...
    def __or__(
        self,
        next: PFn[Tin, Tout] | Sequence[PFn[Tin, Tout]] | Callable[[Task[Iterable[Tout]],Tout], bool]
    ) -> PFn[Tin, Tout]:
        return self._convert_next(next)

