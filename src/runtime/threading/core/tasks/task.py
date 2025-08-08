from __future__ import annotations
from typing import (
    Sequence, TypeVar, Concatenate, ClassVar, Generic, Callable,
    ParamSpec, Any, cast, overload
)

from runtime.threading.core.threading_exception import ThreadingException
from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.event import Event
from runtime.threading.core.one_time_event import OneTimeEvent
from runtime.threading.core.continue_when import ContinueWhen
from runtime.threading.core.lock import Lock
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.tasks.task_state import TaskState
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.tasks_continuation import TasksContinuation
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.tasks.task_exception import TaskException
from runtime.threading.core.tasks.helpers import get_function_name
from runtime.threading.core.parallel.pipeline.p_context import PContext

P = ParamSpec("P")
T = TypeVar("T")
Tresult = TypeVar("Tresult")
Tcontinuation = TypeVar("Tcontinuation")

TaskCompletedError = TaskException("Task is completed")
TaskNotScheduledError = TaskException("Task is not scheduled to start")
TaskAlreadyRunningError = TaskException("Task is already running")
TaskAlreadyScheduledError = TaskException("Task is already scheduled (on this or another scheduler)")
AwaitedTaskInterruptedError = TaskException("One or more awaited tasks were interrupted")

LOCK = Lock()

class TaskProto:
    """The TaskProto class is a Task creation wrapper, used to create new tasks in an easy way.
    """
    __slots__ = [ "__name", "__interrupt", "__scheduler", "__lazy" ]
    __default__: ClassVar[TaskProto | None] = None

    def __new__(
        cls,
        name: str | None = None,
        interrupt: Interrupt | None = None,
        scheduler: TaskScheduler | None = None,
        lazy: bool | None = None
    ):
        if name is interrupt is scheduler is lazy is None:
            if TaskProto.__default__ is None:
                TaskProto.__default__ = super().__new__(cls)
            return TaskProto.__default__
        else:
            return super().__new__(cls)

    def __init__(
        self,
        name: str | None = None,
        interrupt: Interrupt | None = None,
        scheduler: TaskScheduler | None = None,
        lazy: bool | None = None
    ):
        self.__name = name
        self.__interrupt = interrupt
        self.__scheduler = scheduler
        self.__lazy = lazy or False

    def plan(
        self,
        fn: Callable[Concatenate[Task[T], P], T],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[T]:
        """Creates a new task without scheduling it.

        Args:
            fn (Callable[Concatenate[Task[T], P], T]): The target function.

        Returns:
            Task[T]: Returns the new task.
        """
        def fn_wrap(task: Task[T]) -> T:
            return fn(task, *args, **kwargs)

        if self.__scheduler:
            raise ThreadingException("Future tasks cannot have scheduler specified") # pragma: no cover

        return Task[T](fn_wrap, self.__name, self.__interrupt, self.__lazy)

    def run(
        self,
        fn: Callable[Concatenate[Task[T], P], T], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[T]:
        """Creates a new task and schedules it.

        Args:
            fn (Callable[Concatenate[Task[T], P], T]): The target function.

        Returns:
            Task[T]: Returns the new task.
        """
        def fn_wrap(task: Task[T]) -> T:
            return fn(task, *args, **kwargs)

        if self.__scheduler is None:
            if ( pc := PContext.current() ) and pc is not PContext.root():
                self.__scheduler = pc.scheduler

        task = Task[T](fn_wrap, self.__name, self.__interrupt, self.__lazy)
        task.schedule(self.__scheduler or TaskScheduler.current())
        return task

    def run_after(
        self,
        time: float,
        fn: Callable[Concatenate[Task[T], P], T],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[T]:
        """Creates a new task which will be scheduled after specified time.

        Args:
            time (float): The time (seconds) to wait before scheduling the task.
            fn (Callable[Concatenate[Task[T], P], T]): The target function.

        Returns:
            Task[T]: Returns the new task.
        """
        def fn_sleep(task: Task[Any]) -> None:
            task.interrupt.wait(time)

        def fn_continue(task: Task[Any], other: Task[Any], *args: P.args, **kwargs: P.kwargs) -> T:
            return fn(task, *args, **kwargs)

        if self.__scheduler is None:
            if ( pc := PContext.current() ) and pc is not PContext.root():
                self.__scheduler = pc.scheduler

        return Task.create(interrupt = self.__interrupt).run(fn_sleep).continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE, fn_continue, *args, **kwargs)

class ContinuationProto:
    """The ContinuationProto class is a Task creation wrapper, used to create task continuations in an easy way.
    """
    __slots__ = [ "__tasks", "__name", "__interrupt", "__when", "__options" ]

    def __init__(
        self,
        tasks: Sequence[Task[Any]],
        when: ContinueWhen, /,
        options: ContinuationOptions = ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        name: str | None = None,
        interrupt: Interrupt | None = None
    ):
        self.__tasks = tasks
        self.__when = when
        self.__options = options
        self.__name = name
        self.__interrupt = interrupt

    def plan(self) -> Task[None]:
        """Creates a continuation task which will complete immediately when one or all of the awaited tasks complete.

        Returns:
            Task[None]: Returns a new task.
        """
        continuation = CompletedTask(None)
        setattr(continuation, "_Task__state", TaskState.SCHEDULED)

        Event._add_continuation( # pyright: ignore[reportPrivateUsage]
            tuple(task.wait_event for task in self.__tasks),
            TasksContinuation(self.__when, self.__tasks, continuation, self.__options, self.__interrupt)
        )
        return continuation

    def run(
        self,
        fn: Callable[Concatenate[Task[Tresult], Sequence[Task[Any]], P], Tresult], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        """Creates a continuation task which will run when one or all of the awaited tasks complete.

        Args:
            fn (Callable[Concatenate[Task[Tresult], Sequence[Task[Any]], P], Tresult]): The target function.

        Returns:
            Task[Tresult]: Returns a new task.
        """
        continuation = Task.create(
            name = self.__name or get_function_name(fn),
            interrupt = self.__interrupt
        ).plan(
            fn,
            self.__tasks,
            *args,
            **kwargs
        )

        setattr(continuation, "_Task__state", TaskState.SCHEDULED)

        Event._add_continuation( # pyright: ignore[reportPrivateUsage]
            tuple(task.wait_event for task in self.__tasks),
            TasksContinuation(self.__when, self.__tasks, continuation, self.__options, self.__interrupt)
        )

        return continuation

class Task(Generic[T]):
    """The Task class is an abstraction of a regular thread, and it represents an application task of work.
    """
    __slots__ = [
        "__id", "__name", "__parent", "__scheduler", "__pctx", "__internal_event", "__lock", "__weakref__",
        "__target", "__exception", "__state", "__interrupt", "__lazy", "__result", "__target_name"
    ]
    __current_id__: ClassVar[int] = 1

    def __init__(
        self,
        fn: Callable[[Task[T]], T],
        name: str | None = None,
        interrupt: Interrupt | None = None,
        lazy: bool = False
    ):
        """Creates a new Task. It's recommended to use Task.create(), Task.plan() or Task.run() instead.

        Args:
            fn (Callable[[Task[T]], T]): The target function.
            name (str | None, optional): The name of the task. Defaults to None.
            interrupt (Interrupt | None, optional): An external interrupt used for interruption. Defaults to None.
            lazy (bool, optional): Specifies whether or not this task may be run lazily when awaited. Defaults to False.
        """
        with LOCK:
            self.__id = Task.__current_id__
            Task.__current_id__ += 1

        self.__name = name or f"Task_{self.__id}"
        self.__internal_event = OneTimeEvent(purpose = "TASK_NOTIFY")
        self.__lock = Lock()
        self.__scheduler: TaskScheduler | None = None
        self.__target = fn
        self.__target_name = f"{fn.__module__}.{fn.__qualname__}"
        self.__state: TaskState = TaskState.NOTSTARTED
        self.__interrupt = interrupt or Interrupt.none()
        self.__exception: Exception | None = None
        self.__lazy = lazy
        self.__result: T | None = None
        self.__parent = TaskScheduler.current_task()

        pctx = PContext.current()
        self.__pctx = pctx if pctx is not PContext.root() else None


    @property
    def id(self) -> int:
        """The unique task id.
        """
        return self.__id

    @property
    def name(self) -> str:
        """The task name.
        """
        return self.__name

    @name.setter
    def name(self, value: str):
        """Sets the task name
        """
        self.__name = value or f"Task_{self.__id}"
        TaskScheduler.current()._refresh_task() # pyright: ignore[reportPrivateUsage]

    @property
    def state(self) -> TaskState:
        """The current task state.
        """
        with self.__lock:
            return self.__state

    @property
    def parent(self) -> Task[Any] | None:
        """The parent task (if any).
        """
        return self.__parent

    @property
    def target(self) -> str: # pragma: no cover
        """Returns the name of the target function (for testing).
        """
        return self.__target_name

    @property
    def is_completed(self) -> bool:
        """Indicates if the task is completed or not.
        """
        with self.__lock:
            return self.__state >= TaskState.COMPLETED

    @property
    def is_completed_successfully(self) -> bool:
        """Indicates if the task is successfully completed (ie. ran to end without any exceptions).
        """
        with self.__lock:
            return self.__state == TaskState.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Indicates if the target function raised an exception.
        """
        with self.__lock:
            return self.__state == TaskState.FAILED

    @property
    def is_interrupted(self) -> bool:
        """Indicates if task was interrupted or not. Only tasks which raises a InterruptException
        generated from Interrupt.raise_if_interrupted() method, and from the same InterruptSignal
        are considered interrupted. Simply raising an InterruptExecption will cause task to fail.
        """
        with self.__lock:
            return self.__state == TaskState.INTERRUPTED

    @property
    def is_scheduled(self) -> bool:
        """Indicates if the task is scheduled to run.
        """
        with self.__lock:
            return self.__state == TaskState.SCHEDULED

    @property
    def is_running(self) -> bool:
        """Indicates if the task is running.
        """
        with self.__lock:
            return self.__state == TaskState.RUNNING

    @property
    def is_lazy(self) -> bool:
        """Indicates if task is lazy. If it is, task will be scheduled automatically
        when awaited, or when property Task.result is accessed.
        """
        return self.__lazy

    @property
    def interrupt(self) -> Interrupt:
        """The task Interrupt.
        """
        return self.__interrupt

    @property
    def result(self) -> T:
        """The result of the task (if any). This call will block until task is done,
        and if target function raised an exception, that exception will be re-raised here.
        If task is not scheduled and is lazy, it will be run automatically.
        """
        with self.__lock:
            if self.__state == TaskState.NOTSTARTED:
                if self.__lazy:
                    TaskScheduler.current().prioritise(self)
                else:
                    raise TaskNotScheduledError
            elif self.__state == TaskState.INTERRUPTED:
                raise cast(Exception, self.__exception)
            elif self.__state == TaskState.FAILED:
                raise cast(Exception, self.__exception)
            else:
                pass

        self.wait()

        with self.__lock:
            if self.__state in (TaskState.INTERRUPTED, TaskState.FAILED):
                raise cast(Exception, self.__exception)

            return cast(T, self.__result)

    @property
    def exception(self) -> Exception | None:
        """The exception raised by target function (if any).
        """
        return self.__exception

    @property
    def wait_event(self) -> Event:
        """The internal task event, signaled upon completion.
        """
        return self.__internal_event

    @staticmethod
    def current() -> Task[Any] | None:
        """Returns the currently running task, if called from within one.
        """
        return TaskScheduler.current_task()


    def schedule(self, scheduler: TaskScheduler | None = None) -> None:
        """Queues the task on the specified scheduler.
        If scheduler is omitted or None, the current or default task scheduler is used (ie. TaskScheduler.current).

        Args:
            scheduler (TaskScheduler, optional): The task scheduler on which to schedule. Defaults to None
        """
        with self.__lock:
            if self.__state == TaskState.SCHEDULED:
                raise TaskAlreadyScheduledError
            elif self.__state >= TaskState.COMPLETED:
                raise TaskCompletedError
            elif self.__state >= TaskState.RUNNING:
                raise TaskAlreadyRunningError # pragma: no cover

            if scheduler == None:
                scheduler = TaskScheduler.current()

            self.__scheduler = scheduler
            self.__transition_to(TaskState.SCHEDULED)
            scheduler.queue(self)

    def run_synchronously(self) -> None:
        """Runs the task synchronously.
        """

        current_scheduler = TaskScheduler.current()

        with self.__lock:
            if self.__state >= TaskState.COMPLETED:
                raise TaskCompletedError
            elif self.__state >= TaskState.RUNNING:
                raise TaskAlreadyRunningError
            elif self.__scheduler != None and self.__scheduler is not current_scheduler:
                raise TaskAlreadyScheduledError # pragma: no cover

            if self.__scheduler == None:
                self.__scheduler = current_scheduler

            self.__transition_to(TaskState.RUNNING)

        try:
            if self.__pctx and not self.__pctx.closed and current_scheduler is self.__pctx.scheduler and PContext._register(self.__pctx): # pyright: ignore[reportPrivateUsage]
                pass
            else:
                self.__pctx = None

            self.__interrupt.raise_if_signaled()
            self.__result = self.__target(self)

            with self.__lock:
                self.__transition_to(TaskState.COMPLETED)

        except InterruptException as ex:
            with self.__lock:
                self.__exception = ex

                if ex.interrupt.signal_id == self.__interrupt.signal_id:
                    self.__transition_to(TaskState.INTERRUPTED)
                # elif ex.interrupt is self.__interrupt:
                #     self.__transition_to(TaskState.INTERRUPTED)
                else:
                    self.__transition_to(TaskState.FAILED)
        except Exception as ex:
            with self.__lock:
                self.__exception = ex
                self.__transition_to(TaskState.FAILED)
        finally:
            if self.__pctx:
                PContext._unregister(self.__pctx) # pyright: ignore[reportPrivateUsage]
                self.__pctx = None

            self.__internal_event.signal()

    def wait(
        self,
        timeout: float | None = None, /,
        interrupt: Interrupt | None = None,
    ) -> bool:
        """Waits for the task to complete. If task has not been scheduled and is lazy,
        it will be run automatically.

        Args:
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Returns:
            bool: Returns True if task completed. Otherwise False.
        """
        with self.__lock:
            if self.__state == TaskState.NOTSTARTED and self.__lazy:
                TaskScheduler.current().prioritise(self)

        return self.__internal_event.wait(timeout, interrupt)


    def continue_with(
        self,
        options: ContinuationOptions,
        fn: Callable[Concatenate[Task[Tcontinuation], Task[T], P], Tcontinuation], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tcontinuation]:
        """Creates and returns a continuation task which is run when this task transitions into
        a state matched by that specified in 'options' argument.

        Args:
            options (ContinuationOptions): Specifies when and how continuation is run.
            fn (Callable[Concatenate[Task[Tcontinuation], Task[T], P], Tcontinuation]): The target function.

        Returns:
            Task[Tcontinuation]: Returns a new Task instance.
        """
        continuation = Task.plan(fn, self, *args, **kwargs)
        continuation.__state = TaskState.SCHEDULED

        Event._add_continuation( # pyright: ignore[reportPrivateUsage]
            (self.wait_event,),
            TasksContinuation(ContinueWhen.ALL, (self,), continuation, options, self.__interrupt)
        )

        return continuation

    def _interrupt_and_notify(self) -> None:
        with self.__lock:
            if self.__state == TaskState.NOTSTARTED:
                raise TaskNotScheduledError # pragma: no cover -- continuation tasks should not be handled directly
            elif self.__state >= TaskState.COMPLETED:
                raise TaskCompletedError # pragma: no cover -- continuation tasks should not be handled directly

            self.__exception = InterruptException(self.__interrupt)
            self.__transition_to(TaskState.INTERRUPTED)
            self.__internal_event.signal()

    def __transition_to(self, state: TaskState) -> None:
        with self.__lock:
            if state == TaskState.SCHEDULED and self.__state == TaskState.NOTSTARTED:
                pass
            elif state == TaskState.RUNNING and self.__state == TaskState.NOTSTARTED:
                pass
            elif state == TaskState.RUNNING and self.__state == TaskState.SCHEDULED:
                pass
            elif state == TaskState.INTERRUPTED and self.__state == TaskState.SCHEDULED:
                pass
            elif state == TaskState.INTERRUPTED and self.__state == TaskState.NOTSTARTED:
                pass
            elif state == TaskState.INTERRUPTED and self.__state == TaskState.RUNNING:
                pass
            elif state == TaskState.FAILED and self.__state == TaskState.RUNNING:
                pass
            elif state == TaskState.COMPLETED and self.__state == TaskState.RUNNING:
                pass
            else:
                raise TaskException(f"Task cannot transition from state '{self.__state.name}' to '{state.name}'")

            self.__state = state

            if state in [TaskState.INTERRUPTED, TaskState.FAILED, TaskState.COMPLETED ]:
                del self.__target

    def __repr__(self) -> str:
        return f"Task '{self.name}' {self.state.name}"

    @staticmethod
    def wait_any(
        tasks: Sequence[Task[Any]],
        timeout: float | None = None, /,
        fail_on_interrupt: bool = False,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Waits for any of the specified tasks to complete.

        Args:
            tasks (Sequence[Task]): The tasks to await.
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            fail_on_interruptl (bool): Raise a AwaitedTaskInterruptedError if any of the tasks was interrupted.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Raises:
            AggregateException: Any failed tasks will raise an AggregateException
            AwaitedTaskInterruptedError: Any interrupted tasks will raise a AwaitedTaskInterruptedError if 'fail_on_interrupted' argument is True

        Returns:
            bool: Returns True when any of the tasks completed. Otherwise False.
        """

        events: Sequence[Event] = [ t.__internal_event for t in tasks ]

        if Event.wait_any(events, timeout, interrupt = interrupt):
            if interrupt and interrupt.is_signaled:
                return False # pragma no cover

            if fail_on_interrupt and [ t.__exception for t in tasks if t.__exception if t.is_interrupted ]:
                raise AwaitedTaskInterruptedError

            exceptions = [ t.__exception for t in tasks if t.__exception if t.is_failed ]

            if len(exceptions) > 0:
                raise AggregateException(exceptions)
            return True
        else:
            return False # pragma: no cover -- events will be hit eventually

    @staticmethod
    def wait_all(
        tasks: Sequence[Task[Any]],
        timeout: float | None = None, /,
        fail_on_interrupt: bool = False,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Waits for all of the specified tasks to complete.

        Args:
            tasks (Sequence[Task]): The tasks to await.
            timeout (float | None, optional): Timeout (seconds) before returning False. Defaults to None.
            fail_on_interrupt (bool): Raise a TasksException if any of the tasks was interrupted.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Raises:
            AggregateException: Any failed tasks will raise an AggregateException
            TasksException: Any interrupted tasks will raise a TasksException if fail_on_interrupted is True

        Returns:
            bool: Returns true if all of the tasks completed. Otherwise False.
        """

        events: Sequence[Event] = [ t.__internal_event for t in tasks ]

        if Event.wait_all(events, timeout, interrupt = interrupt):
            if interrupt and interrupt.is_signaled:
                return False # pragma no cover

            if fail_on_interrupt and [ t.__exception for t in tasks if t.__exception if t.is_interrupted ]:
                raise AwaitedTaskInterruptedError

            exceptions = [ t.__exception for t in tasks if t.__exception if t.is_failed ]

            if len(exceptions) > 0:
                raise AggregateException(exceptions)
            return True
        else:
            return False # pragma: no cover -- events will be hit eventually

    @staticmethod
    def with_any(
        tasks: Sequence[Task[Any]], /,
        options: ContinuationOptions=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        interrupt: Interrupt | None = None
    ) -> ContinuationProto:
        """Initiates the creation of a new continuation which is run when any of the specified tasks are completed.

        Args:
            tasks (Sequence[Task[Any]]): The tasks awaited.
            options (ContinuationOptions): Specifies when and how continuation is run.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Returns:
            ContinuationProto: Returns a ContinuationProto wrapper.
        """
        return ContinuationProto(tasks, ContinueWhen.ANY, options = options, interrupt = interrupt)

    @staticmethod
    def with_all(
        tasks: Sequence[Task[Any]], /,
        options: ContinuationOptions=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        interrupt: Interrupt | None = None,
    ) -> ContinuationProto:
        """Initiates the creation of a new continuation which is run when all of the specified tasks are completed.

        Args:
            tasks (Sequence[Task[Any]]): The tasks awaited.
            options (ContinuationOptions): Specifies when and how continuation is run.
            interrupt (Interrupt | None, optional): An Interrupt for this specific call. Defaults to None.

        Returns:
            ContinuationProto: Returns a ContinuationProto wrapper.
        """
        return ContinuationProto(tasks, ContinueWhen.ALL, options = options, interrupt = interrupt)


    @staticmethod
    def create(
        *,
        name: str | None = None,
        interrupt: Interrupt | None = None,
        scheduler: TaskScheduler | None = None,
        lazy: bool = False
    ) -> TaskProto:
        """Initiates the creation of a new Task.

        Args:
            name (str | None, optional): The name if the task. Defaults to None.
            interrupt (Interrupt | None, optional): An external interrupt used to stop the task. Defaults to None.
            scheduler (TaskScheduler | None, optional): A scheduler onto which the task will be scheduled. Defaults to None.
            lazy (bool, optional): Specifies if task can be lazily started or not. Defaults to False.

        Returns:
            TaskProto: Returns a TaskProto wrapper.
        """
        return TaskProto(name, interrupt, scheduler, lazy)

    @staticmethod
    def plan(
        fn: Callable[Concatenate[Task[Tresult], P], Tresult], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        """Creates a new task without scheduling it.
        Use Task.Create().plan() for more control of the task specifics.

        Args:
            fn (Callable[Concatenate[Task[Tresult], P], Tresult]): The target function.

        Returns:
            Task[Tresult]: Returns a new task.
        """
        return TaskProto().plan(fn, *args, **kwargs)

    @staticmethod
    def run(
        fn: Callable[Concatenate[Task[Tresult], P], Tresult],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        """Creates a new task and schedules it on the default scheduler.
        Use Task.Create().run() for more control of the task specifics.

        Args:
            fn (Callable[Concatenate[Task[Tresult], P], Tresult]): The target function.

        Returns:
            Task[Tresult]: Returns a new task.
        """
        return TaskProto().run(fn, *args, **kwargs)

    @staticmethod
    def run_after(
        time: float,
        fn: Callable[Concatenate[Task[Tresult], P], Tresult], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        """Creates a new task which will be scheduled on the default scheduler after specified time.
        Use Task.Create().run_after() for more control of the task specifics.

        Args:
            time (float): The time in seconds to wait before scheduling the task.
            fn (Callable[Concatenate[Task[Tresult], P], Tresult]): The target function.

        Returns:
            Task[Tresult]: Returns a new task.
        """

        return TaskProto().run_after(time, fn, *args, **kwargs)

    @staticmethod
    def from_result(result: Tresult) -> Task[Tresult]:
        """Creates a task which is completed with a preset result.

        Args:
            result (Tresult): The task result.

        Returns:
            Task[Tresult]: Returns a completed task with specified result.
        """
        task = CompletedTask(result)
        task.run_synchronously()
        return task

class CompletedTask(Task[T]):
    """A task which is already completed, used for immediate continuation chaining.
    """
    @overload
    def __init__(
        self
    ) -> None:
        ...
    @overload
    def __init__(
        self,
        result: T
    ) -> None:
        ...
    def __init__(
        self,
        result: Any | None = None
    ):
        def empty_target(task: Task[Any]) -> Any:
            return result

        super().__init__(empty_target)

