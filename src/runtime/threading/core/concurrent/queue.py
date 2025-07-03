from __future__ import annotations
from typing import TypeVar, Iterable, Iterator, cast
from time import time

from runtime.threading.core.auto_clear_event import AutoClearEvent
from runtime.threading.core.lock import Lock
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.parallel.pipeline.p_iterable import PIterator

T = TypeVar("T")
Tinput = TypeVar("Tinput")
Toutput = TypeVar("Toutput")

class Queue(Iterable[T]):
    """The Queue class is a thread-safe doubly linked FIFO queue.
    """
    __slots__ = ["__head", "__tail", "__lock", "__notify_event"]

    def __init__(self):
        self.__head: Queue.Node | None = None
        self.__tail: Queue.Node | None = None
        self.__lock = Lock()
        self.__notify_event = AutoClearEvent(purpose = "CONCURRENT_QUEUE_NOTIFY")

    @property
    def synchronization_lock(self) -> Lock: # pragma: no cover
        """The internal lock used for synchronization
        """
        return self.__lock

    @staticmethod
    def from_items(items: Iterable[Tinput]) -> Queue[Tinput]:
        """Creates a new queue with preexisting items in it.

        Args:
            items (Iterable[Tinput]): The items to add.

        Returns:
            Queue[Tinput]: Returns a new queue.
        """
        queue: Queue[Tinput] = Queue()
        for item in items:
            queue.enqueue(item)
        return queue

    def enqueue(self, item: T) -> None:
        """Adds an item to the end of the queue.

        Args:
            item (T): The item.
        """
        with self.__lock:
            node = Queue.Node(item, None, self.__head)
            if self.__head:
                self.__head.set_previous(node)
            self.__head = node
            if not self.__tail:
                self.__tail = self.__head

        self.__notify_event.signal()

    def requeue(self, item: T) -> None:
        """Adds an item to the beginning of the queue. This is used in cases when a consumer
        is unsuccessful processing an item, and that item should be processed asap by another.

        Args:
            item (T): The item.
        """
        with self.__lock:
            node = Queue.Node(item, self.__tail, None)
            if self.__tail:
                self.__tail.set_next(node)
            self.__tail = node
            if not self.__head:
                self.__head = self.__tail

        self.__notify_event.signal()

    def try_dequeue(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> tuple[T | None, bool]:
        """Tries to dequeue an item. If queue is empty or a timeout occurs, a default value or 'None, False' is returned.

        Args:
            timeout (float | None, optional): The operation timout. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Returns:
            tuple[T | None, bool]: Returns a tuple containing the dequeued item and the operation result.
        """
        if self.__lock.acquire(timeout, interrupt = interrupt):
            try:
                if self.__tail:
                    node = self.__tail
                    if node.previous:
                        self.__tail = node.previous
                        node.previous.set_next(None)
                    else:
                        self.__tail = None
                        self.__head = None

                    value = node.clear()

                    return value, True
                else:
                    return None, False
            finally:
                self.__lock.release()
        else:
            return None, False # pragma: no cover

    def dequeue(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> T:
        """Dequeues an item. If queue is empty, operation waits for an item to be added.

        Args:
            timeout (float | None, optional): The operation timout. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Raises:
            TimeoutError: Raises a TimeoutError if operation times out.
        """
        t_start = time()
        while True:
            timeout = max(0, timeout-(time()-t_start)) if timeout is not None else None
            result, success = self.try_dequeue(timeout, interrupt)

            if success:
                return cast(T, result)
            elif timeout is None or ( timeout > 0 and self.__notify_event.wait(timeout, interrupt) ):
                if interrupt is not None:
                    interrupt.raise_if_signaled()
            else:
                raise TimeoutError

    def __iter__(self) -> Iterator[T]:
        return Queue.Iterator[T](self)

    def __repr__(self) -> str:
        with self.__lock:
            nodes: list[str] = []
            node = self.__tail

            while node:
                nodes.append(str(node.value))
                node = node.previous

            return f"({', '.join(nodes)})"

    class Iterator(PIterator[Toutput]):
        __slots__ = ["__queue"]

        def __init__(self, queue: Queue[Toutput]):
            self.__queue = queue

        def __next__(self) -> Toutput:
            return self.next()

        def next(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> Toutput:
            result, success = self.__queue.try_dequeue(timeout, interrupt)
            if success:
                return cast(Toutput, result)
            else:
                raise StopIteration


    class Node:
        __slots__ = [ "__value", "__previous", "__next" ]

        def __init__(self, value: T, previous: Queue.Node | None, next: Queue.Node | None):
            self.__value = value
            self.__previous = previous
            self.__next = next

        @property
        def previous(self) -> Queue.Node | None: # pragma: no cover

            return self.__previous
        @property
        def next(self) -> Queue.Node | None: # pragma: no cover
            return self.__next

        @property
        def value(self) -> T: # pragma: no cover
            return self.__value # pyright: ignore[reportReturnType]

        def set_previous(self, node: Queue.Node | None):
            self.__previous = node

        def set_next(self, node: Queue.Node | None):
            self.__next = node

        def clear(self) -> T:
            value = self.__value
            self.__previous = None
            self.__next = None
            self.__value = None
            return value # pyright: ignore[reportReturnType]

        def __repr__(self):
            return str(self.__value) # pragma: no cover
