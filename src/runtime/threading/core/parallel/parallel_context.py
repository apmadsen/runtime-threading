from __future__ import annotations
from typing import Any, ClassVar, MutableSequence, overload
from threading import local

from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.tasks.interrupt_signal import InterruptSignal
from runtime.threading.core.tasks.lock import Lock
from runtime.threading.core.parallel.parallel_exception import ParallelException

LOCK = Lock()
STACKS = local()

class ParallelContext():
    __slots__ = [ "__id", "__max_parallelism", "__scheduler", "__interrupt_signal" ]
    __CURRENT_ID: ClassVar[int] = 0

    @overload
    def __init__(self, max_parallelism: int) -> None:
        """Creates a new parallel context

        Args:
            max_parallelism (int): The max no. of parallel threads.
        """
        ...
    @overload
    def __init__(self, max_parallelism: int, interrupt: Interrupt) -> None:
        """Creates a new parallel context

        Args:
            max_parallelism (int): The max no. of parallel threads.
            interrupt (Interrupt): The Interrupt.
        """
        ...
    @overload
    def __init__(self, max_parallelism: int, interrupt: Interrupt, scheduler: TaskScheduler) -> None:
        """Creates a new parallel context

        Args:
            max_parallelism (int): The max no. of parallel threads.
            interrupt (Interrupt): The Interrupt.
            scheduler (TaskScheduler): The task scheduler.
        """
        ...
    def __init__(self, max_parallelism: int, interrupt: Interrupt = Interrupt.none(), scheduler: TaskScheduler | None = None):
        if max_parallelism < 1:
            raise ValueError("Argument max_parallelism must be greater than 0")

        with LOCK:
            self.__id = ParallelContext.__CURRENT_ID
            ParallelContext.__CURRENT_ID += 1 # type: ignore
        self.__max_parallelism = max_parallelism
        self.__scheduler = scheduler or TaskScheduler.default()
        self.__interrupt_signal = InterruptSignal(interrupt)

    @property
    def id(self) -> int:
        return self.__id

    @property
    def max_parallelism(self) -> int:
        return self.__max_parallelism

    @property
    def scheduler(self) -> TaskScheduler:
        return self.__scheduler

    @property
    def interrupt(self) -> Interrupt:
        return self.__interrupt_signal.interrupt

    @classmethod
    def root(cls) -> ParallelContext:
        """Returns the root parallel context
        """
        with LOCK:
            stack = ParallelContext.__get_stack()
            return stack[0]

    @classmethod
    def current(cls) -> ParallelContext:
        """Returns the current parallel context
        """
        with LOCK:
            stack = ParallelContext.__get_stack()
            return stack[-1]

    @staticmethod
    def __get_stack() -> MutableSequence[ParallelContext]:
        with LOCK:
            if not hasattr(STACKS, "stack") or getattr(STACKS, "stack") is None:
                STACKS.stack = [ParallelContext(2)]
            return STACKS.stack

    def __enter__(self) -> ParallelContext:
        with LOCK:
            stack = ParallelContext.__get_stack()
            stack.append(self)
            return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        with LOCK:
            self.__interrupt_signal.signal() # make sure that any ongoing work is canceled

            del self.__scheduler
            del self.__interrupt_signal

            stack = ParallelContext.__get_stack()

            if not any(stack):
                raise ParallelException(f"PContext Stack error: Context {self.id} already exited")
            elif (current := stack.pop() ) and current != self:
                stack.append(current)
                raise ParallelException(f"PContext Stack error: Context {self.id} exited while nested context is still active")
