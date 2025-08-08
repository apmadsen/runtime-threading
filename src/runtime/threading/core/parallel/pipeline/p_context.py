from __future__ import annotations
from typing import ClassVar, overload
from types import TracebackType
from collections import deque
from threading import local

from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.interrupt_signal import InterruptSignal
from runtime.threading.core.lock import Lock
from runtime.threading.core.parallel.pipeline.pipeline_exception import PipelineException
from runtime.threading.core.defaults import DEFAULT_PARALLELISM

class Stack(local):
    __stack: deque[PContext] | None

    def get(self) -> deque[PContext]:
        if not hasattr(self, "_Stack__stack") or self.__stack is None:
            self.__stack = deque((PContext(DEFAULT_PARALLELISM),))
        return self.__stack

    def try_register(self, context: PContext) -> bool:
        if not hasattr(self, "_Stack__stack") or self.__stack is None:
            self.__stack = deque((context,))
            return True
        elif len(self.__stack) == 0:
            self.__stack.append(context)
            return True
        else: # pragma: no cover
            return False

    def try_unregister(self, context: PContext) -> bool:
        if self.__stack and len(self.__stack) == 1 and self.__stack[0] == context:
            self.__stack.clear()
            return True
        else: # pragma: no cover
            return False

LOCK = Lock()
STACK = Stack()

class PContext():
    """The PContext class is used for setting up parallel contexts which in turn provides parallelism options,
    interrupts and schedulers to parallel pipelines.
    """

    __slots__ = [ "__id", "__max_parallelism", "__scheduler", "__interrupt_signal", "__closed" ]
    __current__id__: ClassVar[int] = 0

    @overload
    def __init__(self, max_parallelism: int, /) -> None:
        """Creates a new parallel context.

        Args:
            max_parallelism (int): The max no. of parallel threads.
        """
        ...
    @overload
    def __init__(
        self,
        max_parallelism: int, /,
        interrupt: Interrupt | None = None,
        scheduler: TaskScheduler | None = None
    ) -> None:
        """Creates a new parallel context.

        Args:
            max_parallelism (int): The max no. of parallel threads.
            interrupt (Interrupt): The Interrupt.
            scheduler (TaskScheduler): The task scheduler.
        """
        ...
    def __init__(
        self,
        max_parallelism: int, /,
        interrupt: Interrupt | None = None,
        scheduler: TaskScheduler | None = None
    ):
        if max_parallelism < 1:
            raise ValueError("Argument max_parallelism must be greater than 0") # pragma: no cover

        with LOCK:
            self.__id = PContext.__current__id__
            PContext.__current__id__ += 1

        self.__closed = False
        self.__max_parallelism = max_parallelism
        self.__scheduler = scheduler or TaskScheduler.default()
        self.__interrupt_signal = InterruptSignal(interrupt) if interrupt is not None else InterruptSignal()

    @property
    def id(self) -> int:
        """The ID of the PContext instance.
        """
        return self.__id # pragma: no cover

    @property
    def max_parallelism(self) -> int:
        """The max degree of parallelism a parallel operation should use.
        """
        return self.__max_parallelism

    @property
    def closed(self) -> bool:
        """Returns True when PContext has been closed/exited.
        """
        return self.__closed

    @property
    def scheduler(self) -> TaskScheduler:
        """The scheduler for internal tasks.
        """
        return self.__scheduler

    @property
    def interrupt(self) -> Interrupt:
        """The external Interrupt used to interrupt a parallel operation.
        """
        return self.__interrupt_signal.interrupt

    @staticmethod
    def root() -> PContext:
        """Returns the root parallel context. This is created automatically on a per-thread basis.
        """
        with LOCK:
            return STACK.get()[0]

    @staticmethod
    def current() -> PContext:
        """Returns the current parallel context. Defaults to the root context.
        """
        with LOCK:
            return STACK.get()[-1]

    @staticmethod
    def _register(parent: PContext) -> bool:
        """Used internally by tasks to register the context that the task was created in
        as a child context to the thread used by the task."""
        with LOCK:
            return STACK.try_register(parent)

    @staticmethod
    def _unregister(parent: PContext) -> bool:
        """Used internally by tasks to unregister the context that the task was created in
        as a child context to the thread used by the task."""
        with LOCK:
            return STACK.try_unregister(parent)

    def __enter__(self) -> PContext:
        with LOCK:
            stack = STACK.get()
            stack.append(self)
            return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None):
        with LOCK:
            self.__interrupt_signal.signal() # make sure that any ongoing work is interrupted

            self.__closed = True
            del self.__scheduler
            del self.__interrupt_signal

            stack = STACK.get()

            if not any(stack): # pragma: no cover
                raise PipelineException(f"PContext Stack error: Context {self.id} already exited")
            elif (current := stack.pop() ) and current != self: # pragma: no cover
                stack.append(current)
                raise PipelineException(f"PContext Stack error: Context {self.id} exited while nested context is still active")