from __future__ import annotations
from typing import Any, Callable, ContextManager, cast
from types import TracebackType
from threading import Thread, Event as TEvent, current_thread
from contextlib import nullcontext

from runtime.threading.core.threading_exception import ThreadingException
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler, TaskAlreadyStartedOrScheduledError, SchedulerClosedError
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.tasks.task_state import TaskState
from runtime.threading.core.one_time_event import OneTimeEvent
from runtime.threading.core.concurrent.queue import Queue
from runtime.threading.core.interrupt_signal import InterruptSignal
from runtime.threading.core.defaults import TASK_KEEP_ALIVE, DEFAULT_PARALLELISM, POLL_INTERVAL


class ConcurrentTaskScheduler(TaskScheduler):
    """The ConcurrentTaskScheduler class is a task scheduler for concurrent workloads,
    with a predefined max degree of parallelism.
    """
    __slots__ = [ "__max_parallelism", "__queue",
                  "__threads", "__active_threads", "__suspended_threads",
                  "__keep_alive", "__close", "__closed" ]

    def __init__(
        self,
        max_parallelism: int = DEFAULT_PARALLELISM,
        keep_alive: float = TASK_KEEP_ALIVE
    ):
        """Creates a new ConcurrentTaskScheduler instance.

        Arguments:
            max_parallelism (int, optional): The max degree of parallelism. Defaults to the no. of CPUs
            keep_alive (float, optional): The no. of seconds to keep threads alive, before reclaiming them. Defaults to 0.1
        """
        super().__init__()

        if max_parallelism < 1: # pragma: no cover
            raise ValueError("Argument max_parallelism must be greater than 0")

        self.__max_parallelism = max_parallelism
        self.__keep_alive = keep_alive
        self.__queue: Queue[Task[Any] | TEvent] = Queue()
        self.__threads: list[Thread] = []
        self.__active_threads: list[Thread] = []
        self.__suspended_threads: list[Thread] = []
        self.__close = InterruptSignal()
        self.__closed: OneTimeEvent | None = None

    @property
    def is_closed(self) -> bool:
        """Returns True if scheduler is closed.
        """
        return self.__closed is not None

    @property
    def max_parallelism(self) -> int:
        """The max degree of parallelism i.e. no. active tasks.
        """
        return self.__max_parallelism

    @property
    def keep_alive(self) -> float:
        """The no. of seconds to keep threads alive, before reclaiming them.
        """
        return self.__keep_alive

    @property
    def allocated_threads(self) -> int:
        """The no. of currently allocated threads. This does not include suspended threads.
        """
        with self.synchronization_lock:
            return len(self.__threads)

    @property
    def active_threads(self) -> int:
        """The no. of currently active threads.
        """
        return len(self.__active_threads)

    @property
    def suspended_threads(self) -> int:
        """The no. of currently suspended threads.
        """
        return len(self.__suspended_threads)

    def queue(self, task: Task[Any]) -> None:
        """Queues the task. Should not be called directly - use Task.schedule(scheduler) instead...

        Arguments:
            task (Task): The task to schedule
        """
        with self.synchronization_lock:
            if self.__closed is not None:
                raise SchedulerClosedError

            if len(self.__active_threads) < self.__max_parallelism:
                thread = Thread(target=self.__run, name = task.name, args=(task,))
                self.__active_threads.append(thread)
                thread.start()
            else:
                self.__queue.enqueue(task)

    def prioritise(self, task: Task[Any]) -> None:
        """Runs the task inline of another.

        Arguments:
            task (Task): The task to run
        """
        with self.synchronization_lock:
            if self.__closed is not None:
                raise SchedulerClosedError # pragma: no cover

            if task.state > TaskState.SCHEDULED or ( task.state == TaskState.SCHEDULED and task not in self.__queue ):
                raise TaskAlreadyStartedOrScheduledError # pragma: no cover

            if ( current_task := self.current_task() ) and current_task.state == TaskState.RUNNING:
                super()._run(task)
                super()._resume(current_task)
            else:
                task.schedule(self)

    def suspend(self) -> ContextManager[Any]:
        """Suspends the current task, ie. when waiting on an event or lock.
        If called from a thread not created by this scheduler, nothing is changed.
        """
        task = cast(Task[Any], self.current_task())
        thread = current_thread()

        with self.synchronization_lock:
            if not task or thread in self.__suspended_threads:
                return nullcontext()
            elif thread not in self.__active_threads:
                return nullcontext() # pragma: no cover
            else:
                org_name = task.name
                task.name += " *SUSPENDED"
                self._refresh_task()


                # add a new task so that no. of active tasks remains the same after the current is suspended
                self.__suspended_threads.append(thread)
                self.__active_threads.remove(thread)
                new_thread = Thread(target=self.__run, args=(None,), name="ConcurrentTaskScheduler.Non-Assigned-Thread")
                new_thread.start()


                def resume() -> None:
                    resume_thread = current_thread()

                    if resume_thread != thread: # pragma: no cover
                        raise ThreadingException("Cannot resume task on a different thread than the one that suspended it")

                    task.name = org_name + " *RESUMING"
                    self._refresh_task()

                    event = TEvent()

                    self.__queue.enqueue(event)

                    with self.synchronization_lock:
                        if len(self.__active_threads) < self.__max_parallelism:
                            new_thread = Thread(target=self.__run, args=(None,), name="ConcurrentTaskScheduler.Resume-Thread")
                            new_thread.start()

                    while not event.wait(POLL_INTERVAL):
                        # python core event may in some edge cases never be called in cases
                        # where scheduler is closed prior to completing all its tasks, so it's
                        # necessary to poll the event and check if close interrupt is signaled
                        # as a precaution
                        self.__close.interrupt.raise_if_signaled() # pragma: no cover

                    task.name = org_name
                    self._refresh_task()

                    with self.synchronization_lock:
                        self.__suspended_threads.remove(resume_thread)
                        self.__active_threads.append(resume_thread)

                return ConcurrentTaskScheduler._SuspendedTask(resume)

    def close(self) -> None:
        """Closes the scheduler and waits for any scheduled tasks to finish.
        """
        if self is TaskScheduler.default() and not self.finalizing:
            raise ThreadingException("Cannot close default scheduler") # pragma: no cover

        self._close()

    def _close(self) -> None:
        if self.__closed is not None:
            return

        wait_for_close = False
        with self.synchronization_lock:
            self.__closed = OneTimeEvent(purpose = "CONCURRENT_TASK_SCHEDULER_CLOSE")
            self.__close.signal()
            wait_for_close = self.allocated_threads > 0

        if wait_for_close:
            self.__closed.wait()



    def __enter__(self) -> ConcurrentTaskScheduler:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None):
        self.close()

    def __run(self, task: Task[Any] | TEvent | None) -> None:
        thread = current_thread()
        keep_alive = True # keep current thread alive i.e. poll for tasks

        try:
            with self.synchronization_lock:
                if thread not in self.__active_threads:
                    self.__active_threads.append(thread)
                self._register()

            while keep_alive:
                try:
                    while True:
                        try:
                            if isinstance(task, Task):
                                super()._run(cast(Task[Any], task))
                            elif isinstance(task, TEvent):
                                task.set()
                                break

                        finally:
                            with self.synchronization_lock:
                                if len(self.__active_threads) > self.__max_parallelism:
                                    self.__active_threads.remove(thread)
                                    keep_alive = False
                                    break

                            task = self.__queue.dequeue(timeout = self.__keep_alive)

                except TimeoutError:
                    try:
                        task = self.__queue.dequeue(timeout = self.__keep_alive)
                    except TimeoutError:
                        with self.synchronization_lock:
                            if thread in self.__active_threads:
                                self.__active_threads.remove(thread)
                            else:
                                pass # pragma: no cover

                        keep_alive = False

        finally:
            with self.synchronization_lock:
                self._unregister()
                if self.__closed is not None:
                    if len(self.__threads) == 0 and len(self.__suspended_threads) == 0:
                        self.__closed.signal()

    def _register(self) -> None:
        """Registers the current thread on the task scheduler.
        """
        with self.synchronization_lock:
            super()._register()
            cur_thread = current_thread()
            self.__threads.append(cur_thread)

    def _unregister(self) -> None:
        """Un-registers the current thread on the task scheduler.
        """
        with self.synchronization_lock:
            super()._unregister()
            cur_thread = current_thread()
            self.__threads.remove(cur_thread)

    def __finalize__(self) -> None:
        self._close() # pragma: no cover

    class _SuspendedTask:
        __slots__ = ["__resume"]
        def __init__(self, fn_resume: Callable[[], None]):
            self.__resume = fn_resume

        def __enter__(self):
            return self

        def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None):
            self.__resume()
