from __future__ import annotations
from typing import Any, ClassVar, overload
from collections import deque
from multiprocessing import cpu_count as get_cpu_count
from threading import local

from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.interrupt_signal import InterruptSignal
from runtime.threading.core.lock import Lock
from runtime.threading.core.parallel.pipeline.pipeline_exception import PipelineException

LOCK = Lock()
class Stack(local):
    __stack: deque[PContext] | None

    def get(self) -> deque[PContext]:
        if not hasattr(self, "_Stack__stack") or self.__stack is None:
            self.__stack = deque((PContext(get_cpu_count()),))
        return self.__stack

    def try_register(self, context: PContext) -> bool:
        if not hasattr(self, "_Stack__stack") or self.__stack is None:
            self.__stack = deque((context,))
            return True
        elif len(self.__stack) == 0:
            self.__stack.append(context)
            return True
        else:
            return False

    def try_unregister(self, context: PContext) -> bool:
        if self.__stack and len(self.__stack) == 1 and self.__stack[0] == context:
            self.__stack.clear()
            return True
        else:
            return False


STACK = Stack()
class PContext():
    __slots__ = [ "__id", "__max_parallelism", "__scheduler", "__interrupt_signal" ]
    __current__id__: ClassVar[int] = 0

    @overload
    def __init__(self, max_parallelism: int, /) -> None:
        """Creates a new parallel context

        Args:
            max_parallelism (int): The max no. of parallel threads.
        """
        ...
    @overload
    def __init__(self, max_parallelism: int, /, interrupt: Interrupt | None = None, scheduler: TaskScheduler | None = None) -> None:
        """Creates a new parallel context

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
        self.__max_parallelism = max_parallelism
        self.__scheduler = scheduler or TaskScheduler.default()
        self.__interrupt_signal = InterruptSignal(interrupt) if interrupt is not None else InterruptSignal()

    @property
    def id(self) -> int:
        return self.__id # pragma: no cover

    @property
    def max_parallelism(self) -> int:
        return self.__max_parallelism

    @property
    def scheduler(self) -> TaskScheduler:
        return self.__scheduler

    @property
    def interrupt(self) -> Interrupt:
        return self.__interrupt_signal.interrupt

    @staticmethod
    def root() -> PContext:
        """Returns the root parallel context
        """
        with LOCK:
            return STACK.get()[0]

    @staticmethod
    def current() -> PContext:
        """Returns the current parallel context
        """
        with LOCK:
            return STACK.get()[-1]

    @staticmethod
    def register(parent: PContext) -> bool:
        with LOCK:
            return STACK.try_register(parent)

    @staticmethod
    def unregister(parent: PContext) -> bool:
        with LOCK:
            return STACK.try_unregister(parent)

    def __enter__(self) -> PContext:
        with LOCK:
            stack = STACK.get()
            stack.append(self)
            return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        with LOCK:
            self.__interrupt_signal.signal() # make sure that any ongoing work is canceled

            del self.__scheduler
            del self.__interrupt_signal

            stack = STACK.get()

            if not any(stack): # pragma: no cover
                raise PipelineException(f"PContext Stack error: Context {self.id} already exited")
            elif (current := stack.pop() ) and current != self: # pragma: no cover
                stack.append(current)
                raise PipelineException(f"PContext Stack error: Context {self.id} exited while nested context is still active")