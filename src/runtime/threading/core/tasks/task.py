from __future__ import annotations
from typing import (
    Sequence, TypeVar, Concatenate, ClassVar, Generic, Callable,
    ParamSpec, Any, cast, overload, TYPE_CHECKING
)
from weakref import WeakKeyDictionary

from runtime.threading.core.tasks.aggregate_exception import AggregateException
from runtime.threading.core.tasks.task_exception import TaskException
from runtime.threading.core.tasks.threading_exception import ThreadingException
from runtime.threading.core.tasks.task_interrupt_exception import TaskInterruptException
from runtime.threading.core.tasks.event import Event
from runtime.threading.core.tasks.lock import Lock
from runtime.threading.core.tasks.task_state import TaskState
from runtime.threading.core.tasks.continuation_options import ContinuationOptions
from runtime.threading.core.tasks.continuation import Continuation
from runtime.threading.core.tasks.continue_when import ContinueWhen
from runtime.threading.core.tasks.interrupt import Interrupt
from runtime.threading.core.tasks.interrupt_signal import InterruptSignal
from runtime.threading.core.tasks.task_continuation import TaskContinuation
from runtime.threading.core.tasks.tasks_continuation import TasksContinuation
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler

if TYPE_CHECKING:
    from runtime.threading.core.tasks.event import Event

P = ParamSpec("P")
T = TypeVar("T")
Tresult = TypeVar("Tresult")
Tcontinuation = TypeVar("Tcontinuation")

LOCK = Lock()
CONTINUATIONS: WeakKeyDictionary[Event, list[Continuation]] = WeakKeyDictionary()

class TaskProto:
    __slots__ = [ "__name", "__interrupt", "__scheduler", "__lazy" ]

    def __init__(
        self,
        name: str | None = None,
        interrupt: Interrupt = Interrupt.none(),
        scheduler: TaskScheduler | None = None,
        lazy: bool = False
    ):
        self.__name = name
        self.__interrupt = interrupt
        self.__scheduler = scheduler
        self.__lazy = lazy

    def run(
        self,
        fn: Callable[Concatenate[Task[T], P], T], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[T]:
        def fn_wrap(task: Task[T]) -> T:
            return fn(task, *args, **kwargs)

        task = Task[T](fn_wrap, self.__name, self.__interrupt, self.__lazy)
        task.schedule(self.__scheduler or TaskScheduler.current())
        return task

    def future(
        self,
        fn: Callable[Concatenate[Task[T], P], T],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[T]:
        def fn_wrap(task: Task[T]) -> T:
            return fn(task, *args, **kwargs)

        return Task[T](fn_wrap, self.__name, self.__interrupt, self.__lazy)


class ContinuationProto:
    __slots__ = [ "__tasks", "__name", "__interrupt", "__when", "__options" ]

    def __init__(
        self,
        tasks: Sequence[Task[Any]],
        when: ContinueWhen, /,
        options: ContinuationOptions = ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        name: str | None = None,
        interrupt: Interrupt = Interrupt.none()
    ):
        self.__tasks = tasks
        self.__when = when
        self.__options = options
        self.__name = name
        self.__interrupt = interrupt

    def task(self) -> Task[None]:
        continuation = CompletedTask(None)
        setattr(continuation, "_Task__state", TaskState.SCHEDULED)
        getattr(Task, "_Task__add_continuation")(self.__tasks, TasksContinuation(self.__when, self.__tasks, continuation, self.__options))

        return continuation

    def then(
        self,
        fn: Callable[Concatenate[Task[Tresult], Sequence[Task[Any]], P], Tresult], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:

        continuation = Task.create(
            name = self.__name or get_function_name(fn),
            interrupt = self.__interrupt
        ).future(
            fn,
            self.__tasks,
            *args,
            **kwargs
        )

        setattr(continuation, "_Task__state", TaskState.SCHEDULED)
        getattr(Task, "_Task__add_continuation")(self.__tasks, TasksContinuation(self.__when, self.__tasks, continuation, self.__options))

        return continuation

class Task(Generic[T]):
    """A basic task

    Arguments:
        Generic (type): The result/output type (optional)
    """
    __slots__ = [
        "__id", "__name", "__parent", "__scheduler", "__internal_event", "__lock", "__weakref__",
        "__target", "__exception", "__state", "__interrupt", "__interrupt_signal", "__lazy", "__result"
    ]
    __current_id__: ClassVar[int] = 1

    def __init__(
        self,
        fn: Callable[[Task[T]], T],
        name: str | None = None,
        interrupt: Interrupt = Interrupt.none(),
        lazy: bool = False
    ):
        with LOCK:
            self.__id = Task.__current_id__
            Task.__current_id__ += 1

        self.__name = name or f"Task_{self.__id}"
        self.__internal_event = Event()
        self.__lock = Lock()
        self.__scheduler: TaskScheduler | None = None
        self.__target = fn
        self.__state: TaskState = TaskState.NOTSTARTED
        self.__interrupt_signal = InterruptSignal(interrupt)
        self.__interrupt = self.__interrupt_signal.interrupt
        self.__exception: Exception | None = None
        self.__lazy = lazy
        self.__result: T | None = None
        self.__parent = TaskScheduler.current_task()


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
        TaskScheduler.current()._refresh_task() # type: ignore[reportPrivateUsage]

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
        """Indicates if task was canceled or not. Only tasks which raises a TaskCanceledException generated from Interrupt.raise_if_canceled() method, are considered canceled.
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
                    raise TaskException("Task is not scheduled to start")
            elif self.__state == TaskState.CANCELED:
                raise cast(Exception, self.__exception)
            elif self.__state == TaskState.FAILED:
                raise cast(Exception, self.__exception)
            elif self.__state == TaskState.SCHEDULED:
                pass

        self.wait()
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
                raise TaskException("Task is already scheduled")
            elif self.__state >= TaskState.COMPLETED:
                raise TaskException("Task is already done")
            elif self.__state >= TaskState.RUNNING:
                raise TaskException("Task is already running")

            if scheduler == None:
                scheduler = TaskScheduler.current()

            self.__scheduler = scheduler
            self.__transition_to(TaskState.SCHEDULED)
            scheduler.queue(self)

    def run_synchronously(self) -> None:
        """Runs the task synchronously.
        """
        try:
            with self.__lock:
                if self.__state >= TaskState.COMPLETED:
                    raise TaskException("Task is already completed")
                elif self.__state >= TaskState.RUNNING:
                    raise TaskException("Task is already running")
                elif self.__state == TaskState.CANCELED:
                    return None
                elif self.__scheduler != None and self.__scheduler != TaskScheduler.current():
                    raise TaskException("Task is already scheduled on another scheduler")

                self.__interrupt.raise_if_signaled()

                if self.__scheduler == None:
                    self.__scheduler = TaskScheduler.current()

                self.__transition_to(TaskState.RUNNING)

            self.__result = self.__target(self)

            with self.__lock:
                self.__transition_to(TaskState.COMPLETED)

        except TaskInterruptException as ex:
            with self.__lock:
                self.__exception = ex

                if ex.interrupt == self.__interrupt:
                    self.__transition_to(TaskState.CANCELED)
                else:
                    self.__transition_to(TaskState.FAILED)
        except Exception as ex:
            with self.__lock:
                self.__exception = ex
                self.__transition_to(TaskState.FAILED)
        finally:
            self.__internal_event.set()
            Task.__notify_continuations(self)

    def cancel(self) -> None:
        """Signals the tasks Interrupt
        """
        self.__interrupt_signal.signal()

    def wait(self, timeout: float | None = None, interrupt: Interrupt = Interrupt.none(), ignore_cancellation: bool = False) -> bool:
        """Waits for the task to complete.
        If task was canceled, a TaskCanceledException will be raised (unless ignore_cancellation is set to True)

        Args:
            timeout (float, optional): The timeout in seconds. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to Interrupt.none().
            ignore_cancellation (bool, optional) -- Specifies whether or not to raise a TaskCanceledException if task was canceled. Defaults to False

        Returns:
            bool: A boolean value indicating if task completed or a timeout occurred
        """
        # # should an Exception be raised, if task is not scheduled???
        # with self.__lock:
        #     if self.__state == TaskState.NOTSTARTED:
        #         raise Exception("Task is not cheduled to start")

        result = Event.wait_any([self.__internal_event, interrupt.wait_event], timeout)

        with self.__lock:
            if self.is_canceled and ignore_cancellation:
                return True
            elif self.__exception != None:
                raise self.__exception
            return result

    def continue_with(
        self,
        options: ContinuationOptions,
        fn: Callable[Concatenate[Task[Tcontinuation], Task[T], P], Tcontinuation], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tcontinuation]:
        continuation = Task.future(fn, self, *args, **kwargs)
        continuation.__state = TaskState.SCHEDULED
        Task.__add_continuation([self], TaskContinuation(self, continuation, options))
        return continuation

    def _cancel_and_notify(self) -> None:
        with self.__lock:
            if self.__state == TaskState.NOTSTARTED:
                raise TaskException("Task is not cheduled to start")
            elif self.__state >= TaskState.COMPLETED:
                raise TaskException("Task is completed")

            self.__exception = TaskInterruptException(self.__interrupt)
            self.__transition_to(TaskState.CANCELED)
            self.__internal_event.set()
            Task.__notify_continuations(self)

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

    @staticmethod
    def wait_any(tasks: Sequence[Task[Any]], timeout: float | None = None, *, fail_on_cancel: bool = False) -> bool:
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

        if Event.wait_any(events, timeout):
            if fail_on_cancel and [ t.__exception for t in tasks if t.__exception if t.is_canceled ]:
                raise ThreadingException("One or more awaited tasks were canceled")

            exceptions = [ t.__exception for t in tasks if t.__exception if t.is_failed ]

            if len(exceptions) > 0:
                raise AggregateException(exceptions)
            return True
        else:
            return False

    @staticmethod
    def wait_all(tasks: Sequence[Task[Any]], timeout: float | None = None, *, fail_on_cancel: bool = False) -> bool:
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
        if Event.wait_all(events, timeout):
            if fail_on_cancel and [ t.__exception for t in tasks if t.__exception if t.is_canceled ]:
                raise ThreadingException("One or more awaited tasks were canceled")

            exceptions = [ t.__exception for t in tasks if t.__exception if t.is_failed ]

            if len(exceptions) > 0:
                raise AggregateException(exceptions)
            return True
        else:
            return False

    @staticmethod
    def with_any(
        tasks: Sequence[Task[Any]],
        *,
        options: ContinuationOptions=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        interrupt: Interrupt = Interrupt.none(),
    ) -> ContinuationProto:
        return ContinuationProto(tasks, ContinueWhen.ANY, options = options, interrupt = interrupt)

    @staticmethod
    def with_all(
        tasks: Sequence[Task[Any]],
        *,
        options: ContinuationOptions=ContinuationOptions.ON_COMPLETED_SUCCESSFULLY,
        interrupt: Interrupt = Interrupt.none(),
    ) -> ContinuationProto:
        return ContinuationProto(tasks, ContinueWhen.ALL, options = options, interrupt = interrupt)


    @staticmethod
    def __add_continuation(tasks: Sequence[Task[Any]], continuation: Continuation) -> None:
        with LOCK:
            already_complete: Sequence[Task[Any]] = []
            for task in tasks:
                if task.is_completed:
                    already_complete.append(task)

                if task.wait_event not in CONTINUATIONS:
                    CONTINUATIONS[task.wait_event] = [continuation]
                else:
                    CONTINUATIONS[task.wait_event].append(continuation)

            for task in already_complete:
                Task.__notify_continuations(task)


    @staticmethod
    def __notify_continuations(task: Task[Any]) -> None:
        with LOCK:
            if task.wait_event in CONTINUATIONS:
                expedited: list[Continuation] = []

                for continuation in list(CONTINUATIONS[task.wait_event]):
                    if continuation.try_continue():
                        expedited.append(continuation)
                        CONTINUATIONS[task.wait_event].remove(continuation)

                for continuation in expedited:
                    for continution_event in continuation.events:
                        if continution_event in CONTINUATIONS:
                            if continuation in CONTINUATIONS[continution_event]:
                                CONTINUATIONS[continution_event].remove(continuation)

                            if len(CONTINUATIONS[continution_event]) == 0:
                                del CONTINUATIONS[continution_event]

    @staticmethod
    def create(
        *,
        name: str | None = None,
        interrupt: Interrupt = Interrupt.none(),
        scheduler: TaskScheduler | None = None,
        lazy: bool = False
    ) -> TaskProto:
        return TaskProto(name, interrupt, scheduler, lazy)


    @staticmethod
    def run(
        fn: Callable[Concatenate[Task[Tresult], P], Tresult],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        return TaskProto().run(fn, *args, **kwargs)

    @staticmethod
    def future(
        fn: Callable[Concatenate[Task[Tresult], P], Tresult], /,
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Task[Tresult]:
        return TaskProto().future(fn, *args, **kwargs)

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

        super().__init__(empty_target, interrupt = Interrupt.none())


def get_function_name(fn: Callable[..., Any]) -> str:
    return f"{fn.__module__}.{fn.__name__}" if fn.__module__ else fn.__name__
