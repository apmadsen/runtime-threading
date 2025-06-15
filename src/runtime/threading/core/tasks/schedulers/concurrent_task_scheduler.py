from __future__ import annotations
from typing import Any, MutableSequence, Callable, ContextManager, cast
from multiprocessing import cpu_count as get_cpu_count
from threading import Thread, Event as IntEvent, current_thread
from contextlib import nullcontext

from runtime.threading.core.interrupt_exception import InterruptException
from runtime.threading.core.threading_exception import ThreadingException
from runtime.threading.core.tasks.schedulers.task_scheduler import TaskScheduler
from runtime.threading.core.tasks.task import Task
from runtime.threading.core.event import Event
from runtime.threading.core.concurrent.queue import Queue
from runtime.threading.core.interrupt_signal import InterruptSignal
from runtime.threading.core.tasks.config import TASK_KEEP_ALIVE

class ConcurrentTaskScheduler(TaskScheduler):
    """A task scheduler for concurrent workloads, with a predefined max degree of parallelism.
    """
    __slots__ = [
        "__max_parallelism", "__queue",
        "__threads", "__active_threads", "__suspended_threads",
        "__keep_alive", "__close", "__closed"
    ]

    def __init__(self, max_parallelism: int = get_cpu_count(), keep_alive: float = TASK_KEEP_ALIVE):
        """Creates a new ConcurrentTaskScheduler instance

        Keyword Arguments:
            max_parallelism (int, optional): The max degree of parallelism. Defaults to the no. of CPUs
            keep_alive (float, optional): The no. of seconds to keep threads alive, before reclaiming them. Defaults to 0.1
        """
        super().__init__()

        if max_parallelism < 1:
            raise ValueError("Argument max_parallelism must be greater than 0")

        self.__max_parallelism = max_parallelism
        self.__keep_alive = keep_alive
        self.__queue: Queue[Task[Any] | IntEvent] = Queue()
        self.__threads: MutableSequence[Thread] = []
        self.__active_threads: MutableSequence[Thread] = []
        self.__suspended_threads: MutableSequence[Thread] = []
        self.__close = InterruptSignal()
        self.__closed: Event | None = None

    @property
    def max_parallelism(self) -> int:
        """The max degree of parallelism
        """
        return self.__max_parallelism

    @property
    def keep_alive(self) -> float:
        """The no. of seconds to keep threads alive, before reclaiming them
        """
        return self.__keep_alive

    @property
    def threads(self) -> int:
        """The no. of currently allocated threads
        """
        with self.synchronization_lock:
            return len(self.__threads)

    @property
    def active_threads(self) -> int:
        """The no. of currently active threads
        """
        return len(self.__active_threads)

    @property
    def suspended_threads(self) -> int:
        """The no. of currently suspended threads
        """
        return len(self.__suspended_threads)

    def queue(self, task: Task[Any]) -> None:
        """Queues the task. Should not be called directly - use Task.schedule(scheduler) instead...

        Arguments:
            task (Task): The task to schedule
        """
        with self.synchronization_lock:
            if self.__closed:
                raise ThreadingException("Task scheduler has been closed")

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
        if current_task := self.current_task():
            TaskScheduler._run(self, task)
            TaskScheduler._resume(self, current_task)
        else:
            task.schedule(self)

    def suspend(self) -> ContextManager[Any]:
        """Suspends the current task, ie. when waiting on an event or lock.
        If called from a thread not created by this scheduler, nothing is changed.
        """
        task = self.current_task()
        thread = current_thread()

        with self.synchronization_lock:
            if not task or thread in self.__suspended_threads:
                return nullcontext()
            elif thread not in self.__active_threads:
                return nullcontext()
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

                    if resume_thread != thread:
                        raise ThreadingException("Cannot resume task on a different thread than the one that suspended it")

                    cast(Task[Any], self.current_task()).name = org_name + " *RESUMING"
                    self._refresh_task()

                    event = IntEvent()

                    self.__queue.enqueue(event)

                    with self.synchronization_lock:
                        if len(self.__active_threads) < self.__max_parallelism:
                            new_thread = Thread(target=self.__run, args=(None,), name="ConcurrentTaskScheduler.Resume-Thread")
                            new_thread.start()

                    event.wait()

                    cast(Task[Any], self.current_task()).name = org_name
                    self._refresh_task()

                    with self.synchronization_lock:
                        self.__suspended_threads.remove(resume_thread)
                        self.__active_threads.append(resume_thread)

                return ConcurrentTaskScheduler._SuspendedTask(resume)

    def close(self) -> None:
        """Closes the scheduler and waits for any scheduled tasks to finish
        """
        wait_for_close = False
        with self.synchronization_lock:
            self.__closed = Event()
            self.__close.signal()
            wait_for_close = self.threads > 0

        if self.__closed and wait_for_close:
            self.__closed.wait()



    def __enter__(self) -> ConcurrentTaskScheduler:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __run(self, task: Task[Any] | IntEvent | None) -> None:
        thread = current_thread()
        try:
            with self.synchronization_lock:
                if thread not in self.__active_threads:
                    self.__active_threads.append(thread)
                self._register()

            keep_alive = True

            while keep_alive:
                try:
                    while True:
                        try:
                            if isinstance(task, Task):
                                if task.is_scheduled: # make sure task has not been and started synchronously
                                    TaskScheduler._run(self, cast(Task[Any], task))
                            elif isinstance(task, IntEvent):
                                task.set()
                                break

                        # except Exception as ex:
                        #     # for debug purposes
                        #     from traceback import print_exc
                        #     print_exc()
                        #     raise
                        finally:
                            with self.synchronization_lock:
                                if len(self.__active_threads) > self.__max_parallelism:
                                    self.__active_threads.remove(thread)
                                    keep_alive = False
                                    break

                            task = self.__queue.dequeue(timeout = self.__keep_alive, interrupt = self.__close.interrupt)

                except (TimeoutError, InterruptException) as ex:
                    if isinstance(ex, InterruptException) and ex.interrupt != self.__close.interrupt:
                        raise

                    if keep_alive:
                        try:
                            task = self.__queue.dequeue(timeout = self.__keep_alive, interrupt = self.__close.interrupt)
                        except (TimeoutError, InterruptException):
                            if isinstance(ex, InterruptException) and ex.interrupt != self.__close.interrupt:
                                raise

                            with self.synchronization_lock:
                                self.__active_threads.remove(thread)

                            keep_alive = False


        finally:
            with self.synchronization_lock:
                self._unregister()
                if self.__closed and len(self.__threads) == 0:
                    self.__closed.set()



    def _register(self) -> None:
        """Registers the current thread on the task scheduler
        """
        super()._register()
        cur_thread = current_thread()
        self.__threads.append(cur_thread)

    def _unregister(self) -> None:
        """Un-registers the current thread on the task scheduler
        """
        super()._unregister()
        cur_thread = current_thread()
        self.__threads.remove(cur_thread)


    class _SuspendedTask:
        __slots__ = ["__resume"]
        def __init__(self, fn_resume: Callable[[], None]):
            self.__resume = fn_resume

        def __enter__(self):
            return self

        def __exit__(self, *exc: Any):
            self.__resume()