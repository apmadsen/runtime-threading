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
from runtime.threading.core.interrupt_signal import InterruptSignal
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
TaskCanceledError = TaskException("Task is canceled")
TaskNotScheduledError = TaskException("Task is not scheduled to start")
TaskAlreadyRunningError = TaskException("Task is already running")
TaskAlreadyScheduledError = TaskException("Task is already scheduled (on this or another scheduler)")
AwaitedTaskCanceledError = TaskException("One or more awaited tasks were canceled")

LOCK = Lock()

class TaskProto:
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
        def fn_sleep(task: Task[Any]) -> None:
            task.interrupt.wait(time)

        def fn_continue(task: Task[Any], other: Task[Any], *args: P.args, **kwargs: P.kwargs) -> T:
            return fn(task, *args, **kwargs)

        if self.__scheduler is None:
            if ( pc := PContext.current() ) and pc is not PContext.root():
                self.__scheduler = pc.scheduler

        return Task.create(interrupt = self.__interrupt).run(fn_sleep).continue_with(ContinuationOptions.ON_COMPLETED_SUCCESSFULLY | ContinuationOptions.INLINE, fn_continue, *args, **kwargs)

class ContinuationProto:
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
        continuation = CompletedTask(None)
        setattr(continuation, "_Task__state", TaskState.SCHEDULED)

        Event.add_continuation(
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

        Event.add_continuation(
            tuple(task.wait_event for task in self.__tasks),
            TasksContinuation(self.__when, self.__tasks, continuation, self.__options, self.__interrupt)
        )

        return continuation

class Task(Generic[T]):
    """A basic task

    Arguments:
        Generic (type): The result/output type (optional)
    """
    __slots__ = [
        "__id", "__name", "__parent", "__scheduler", "__pctx", "__internal_event", "__lock", "__weakref__",
        "__target", "__exception", "__state", "__interrupt", "__interrupt_signal", "__lazy", "__result", "__target_name"
    ]
    __current_id__: ClassVar[int] = 1

    def __init__(
        self,
        fn: Callable[[Task[T]], T],
        name: str | None = None,
        interrupt: Interrupt | None = None,
        lazy: bool = False
    ):
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
        self.__interrupt_signal = InterruptSignal(interrupt) if interrupt is not None else InterruptSignal()
        self.__interrupt = self.__interrupt_signal.interrupt
        self.__exception: Exception | None = None
        self.__lazy = lazy
        self.__result: T | None = None
        self.__parent = TaskScheduler.current_task()

        pctx = PContext.current()
        self.__pctx = pctx if pctx is not PContext.root() else None


    @property
    def id(self) -> int:
        """The unique task id
        """
        return self.__id

    @property
    def name(self) -> str:
        """The unique task name
        """
        return self.__name

    @name.setter
    def name(self, value: str):
        """Sets the unique task name
        """
        self.__name = value or f"Task_{self.__id}"
        TaskScheduler.current()._refresh_task() # pyright: ignore[reportPrivateUsage]

    @property
    def state(self) -> TaskState:
        """The task state
        """
        with self.__lock:
            return self.__state

    @property
    def parent(self) -> Task[Any] | None:
        return self.__parent

    @property
    def target(self) -> str: # pragma: no cover
        """Returns the name of the target (for testing)."""
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
        """Indicates if the task raised an exception.
        """
        with self.__lock:
            return self.__state == TaskState.FAILED

    @property
    def is_canceled(self) -> bool:
        """Indicates if task was canceled or not. Only tasks which raises a InterruptException generated from Interrupt.raise_if_canceled() method, are considered canceled.
        """
        with self.__lock:
            return self.__state == TaskState.CANCELED

    @property
    def is_scheduled(self) -> bool:
        """Indicates if task is scheduled to run.
        """
        with self.__lock:
            return self.__state == TaskState.SCHEDULED

    @property
    def is_running(self) -> bool:
        """Indicates if task is running.
        """
        with self.__lock:
            return self.__state == TaskState.RUNNING

    @property
    def is_lazy(self) -> bool:
        """Indicates if task is lazy.
        """
        return self.__lazy

    @property
    def interrupt(self) -> Interrupt:
        """The task Interrupt.
        """
        return self.__interrupt

    @property
    def result(self) -> T:
        """The result of the task (if any).
        This call will block until task is done, and if task raised an exception, that exception will be re-raised here.
        """
        with self.__lock:
            if self.__state == TaskState.NOTSTARTED:
                if self.__lazy:
                    TaskScheduler.current().prioritise(self)
                else:
                    raise TaskNotScheduledError
            elif self.__state == TaskState.CANCELED:
                raise cast(Exception, self.__exception)
            elif self.__state == TaskState.FAILED:
                raise cast(Exception, self.__exception)
            else:
                pass

        self.wait()

        with self.__lock:
            if self.__state in (TaskState.CANCELED, TaskState.FAILED):
                raise cast(Exception, self.__exception)

            return cast(T, self.__result)

    @property
    def exception(self) -> Exception | None:
        """The task exception (if any).
        """
        return self.__exception

    @property
    def wait_event(self) -> Event:
        """The internal task event, signaled upon completion
        """
        return self.__internal_event

    @staticmethod
    def current() -> Task[Any] | None:
        """Returns the currently running task, if any

        Returns:
            Task | None: The currently running task
        """
        return TaskScheduler.current_task()


    def schedule(self, scheduler: TaskScheduler | None = None) -> None:
        """Queues the task on the specified scheduler.
        If scheduler is omitted or None, the default task scheduler is used (ie. TaskScheduler.default).

        Args:
            scheduler (TaskScheduler, optional): The task scheduler. Defaults to None
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

        with self.__lock:
            if self.__state == TaskState.CANCELED:
                raise TaskCanceledError
            elif self.__state >= TaskState.COMPLETED:
                raise TaskCompletedError
            elif self.__state >= TaskState.RUNNING:
                raise TaskAlreadyRunningError
            elif self.__scheduler != None and self.__scheduler != TaskScheduler.current():
                raise TaskAlreadyScheduledError # pragma: no cover

            if self.__scheduler == None:
                self.__scheduler = TaskScheduler.current()

            self.__transition_to(TaskState.RUNNING)

        try:
            if self.__pctx and TaskScheduler.current() is self.__pctx.scheduler and PContext.register(self.__pctx):
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
                    self.__transition_to(TaskState.CANCELED)
                # elif ex.interrupt is self.__interrupt:
                #     self.__transition_to(TaskState.CANCELED)
                else:
                    self.__transition_to(TaskState.FAILED)
        except Exception as ex:
            with self.__lock:
                self.__exception = ex
                self.__transition_to(TaskState.FAILED)
        finally:
            if self.__pctx:
                PContext.unregister(self.__pctx)
                self.__pctx = None
            self.__internal_event.signal()


    def cancel(self) -> None:
        """Signals the tasks Interrupt
        """
        with self.__lock:
            if self.__state == TaskState.NOTSTARTED:
                self.__transition_to(TaskState.CANCELED)
        self.__interrupt_signal.signal()

    def wait(
        self,
        timeout: float | None = None, /,
        interrupt: Interrupt | None = None,
    ) -> bool:
        """Waits for the task to complete.

        Args:
            timeout (float, optional): The timeout in seconds. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Returns:
            bool: A boolean value indicating if task completed or a timeout occurred
        """

        return self.__internal_event.wait(timeout, interrupt)


    def continue_with(
        self,
        options: ContinuationOptions,
        fn: Callable[Concatenate[Task[Tcontinuation], Task[T], P], Tcontinuation], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tcontinuation]:
        continuation = Task.plan(fn, self, *args, **kwargs)
        continuation.__state = TaskState.SCHEDULED

        Event.add_continuation(
            (self.wait_event,),
            TasksContinuation(ContinueWhen.ALL, (self,), continuation, options, self.__interrupt)
        )

        return continuation

    def _cancel_and_notify(self) -> None:
        with self.__lock:
            if self.__state == TaskState.NOTSTARTED:
                raise TaskNotScheduledError # pragma: no cover -- continuation tasks should not be handled directly
            elif self.__state >= TaskState.COMPLETED:
                raise TaskCompletedError # pragma: no cover -- continuation tasks should not be handled directly

            self.__exception = InterruptException(self.__interrupt)
            self.__transition_to(TaskState.CANCELED)
            self.__internal_event.signal()

    def __transition_to(self, state: TaskState) -> None:
        with self.__lock:
            if state == TaskState.SCHEDULED and self.__state == TaskState.NOTSTARTED:
                pass
            elif state == TaskState.RUNNING and self.__state == TaskState.NOTSTARTED:
                pass
            elif state == TaskState.RUNNING and self.__state == TaskState.SCHEDULED:
                pass
            elif state == TaskState.CANCELED and self.__state == TaskState.SCHEDULED:
                pass
            elif state == TaskState.CANCELED and self.__state == TaskState.NOTSTARTED:
                pass
            elif state == TaskState.CANCELED and self.__state == TaskState.RUNNING:
                pass
            elif state == TaskState.FAILED and self.__state == TaskState.RUNNING:
                pass
            elif state == TaskState.COMPLETED and self.__state == TaskState.RUNNING:
                pass
            else:
                raise TaskException(f"Task cannot transition from state '{self.__state.name}' to '{state.name}'")

            self.__state = state

            if state in [TaskState.CANCELED, TaskState.FAILED, TaskState.COMPLETED ]:
                del self.__target

    def __repr__(self) -> str:
        return f"Task '{self.name}' {self.state.name}"

    @staticmethod
    def wait_any(
        tasks: Sequence[Task[Any]],
        timeout: float | None = None, /,
        fail_on_cancel: bool = False,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Waits for any of the tasks to complete

        Args:
            tasks (Sequence[Task]): The awaited tasks
            timeout (float, optional): The timeout in seconds. Defaults to None
            fail_on_cancel (bool): Raise a TasksException if any task was canceled

        Raises:
            AggregateException: Any failed tasks will raise an AggregateException
            TasksException: Any canceled tasks will raise a TasksException if fail_on_canceled is True

        Returns:
            bool: A boolean value indicating if any of the tasks completed or a timeout occurred
        """

        events: Sequence[Event] = [ t.__internal_event for t in tasks ]

        if Event.wait_any(events, timeout, interrupt = interrupt):
            if interrupt and interrupt.is_signaled:
                return False # pragma no cover

            if fail_on_cancel and [ t.__exception for t in tasks if t.__exception if t.is_canceled ]:
                raise AwaitedTaskCanceledError

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
        fail_on_cancel: bool = False,
        interrupt: Interrupt | None = None
    ) -> bool:
        """Waits for all of the tasks to complete

        Args:
            tasks (Sequence[Task]): The awaited tasks
            timeout (float, optional): The timeout in seconds. Defaults to None
            fail_on_cancel (bool): Raise a TasksException if any task was canceled

        Raises:
            AggregateException: Any failed tasks will raise an AggregateException
            TasksException: Any canceled tasks will raise a TasksException if fail_on_canceled is True

        Returns:
            bool: A boolean value indicating if all of the tasks completed or a timeout occurred
        """

        events: Sequence[Event] = [ t.__internal_event for t in tasks ]

        if Event.wait_all(events, timeout, interrupt = interrupt):
            if interrupt and interrupt.is_signaled:
                return False # pragma no cover

            if fail_on_cancel and [ t.__exception for t in tasks if t.__exception if t.is_canceled ]:
                raise AwaitedTaskCanceledError

            exceptions = [ t.__exception for t in tasks if t.__exception if t.is_failed ]

            if len(exceptions) > 0:
                raise AggregateException(exceptions)
            return True
        else:
            return False # pragma: no cover -- events will be hit eventually

    @staticmethod
    def with_any(
        tasks: Sequence[Task[Any]],
        *,
        options: ContinuationOptions=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        interrupt: Interrupt | None = None,
    ) -> ContinuationProto:
        return ContinuationProto(tasks, ContinueWhen.ANY, options = options, interrupt = interrupt)

    @staticmethod
    def with_all(
        tasks: Sequence[Task[Any]],
        *,
        options: ContinuationOptions=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        interrupt: Interrupt | None = None,
    ) -> ContinuationProto:
        return ContinuationProto(tasks, ContinueWhen.ALL, options = options, interrupt = interrupt)


    @staticmethod
    def create(
        *,
        name: str | None = None,
        interrupt: Interrupt | None = None,
        scheduler: TaskScheduler | None = None,
        lazy: bool = False
    ) -> TaskProto:
        return TaskProto(name, interrupt, scheduler, lazy)

    @staticmethod
    def plan(
        fn: Callable[Concatenate[Task[Tresult], P], Tresult], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        return TaskProto().plan(fn, *args, **kwargs)

    @staticmethod
    def run(
        fn: Callable[Concatenate[Task[Tresult], P], Tresult],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        return TaskProto().run(fn, *args, **kwargs)

    @staticmethod
    def run_after(
        time: float,
        fn: Callable[Concatenate[Task[Tresult], P], Tresult], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        return TaskProto().run_after(time, fn, *args, **kwargs)

    @staticmethod
    def from_result(result: Tresult) -> Task[Tresult]:
        """Creates a task which is completed with a preset result.

        Args:
            result (T): The task result.

        Returns:
            Task[T]: A completed task
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

