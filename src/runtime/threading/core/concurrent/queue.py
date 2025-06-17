from __future__ import annotations
from typing import TypeVar, Iterable, Iterator, cast

from runtime.threading.core.auto_clear_event import AutoClearEvent
from runtime.threading.core.event import Event
from runtime.threading.core.lock import Lock
from runtime.threading.core.interrupt import Interrupt
from runtime.threading.core.parallel.pipeline.p_iterable import PIterator

T = TypeVar("T")
Tinput = TypeVar("Tinput")
Toutput = TypeVar("Toutput")

class Queue(Iterable[T]):
    __slots__ = ["__head", "__tail", "__lock", "__event"]

    def __init__(self):
        self.__head: Queue.Node | None = None
        self.__tail: Queue.Node | None = None
        self.__lock = Lock()
        self.__event = AutoClearEvent()

    @staticmethod
    def from_items(items: Iterable[Tinput]) -> Queue[Tinput]:
        queue: Queue[Tinput] = Queue()
        for item in items:
            queue.enqueue(item)
        return queue

    def enqueue(self, item: T) -> None:
        with self.__lock:
            node = Queue.Node(item, None, self.__head)
            if self.__head:
                self.__head.set_previous(node)
            self.__head = node
            if not self.__tail:
                self.__tail = self.__head

        self.__event.set()

    def requeue(self, item: T) -> None:
        with self.__lock:
            node = Queue.Node(item, self.__tail, None)
            if self.__tail:
                self.__tail.set_next(node)
            self.__tail = node
            if not self.__head:
                self.__head = self.__tail

        self.__event.set()

    def try_dequeue(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> tuple[T | None, bool]:
        """Tries to dequeue an item. If queue is empty, return

        Args:
            timeout (float | None, optional): The operation timout. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Raises:
            TimeoutError: Raises a TimeoutError if operation times out

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
            # raise TimeoutError
            return None, False

    def dequeue(self, timeout: float | None = None, interrupt: Interrupt | None = None) -> T:
        """Dequeues an item. If queue is empty, operation waits for an item to be added.

        Args:
            timeout (float | None, optional): The operation timout. Defaults to None.
            interrupt (Interrupt, optional): The Interrupt. Defaults to None.

        Raises:
            TimeoutError: Raises a TimeoutError if operation times out
        """
        while True:
            result, success = self.try_dequeue(timeout, interrupt)
            if success:
                return cast(T, result)
            elif self.__event.wait(timeout, interrupt):
                if interrupt:
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
