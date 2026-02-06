from typing import Callable, TypeVar, ParamSpec, Any, overload
from runtime.threading.core.lock import Lock
from weakref import WeakKeyDictionary

R = TypeVar("R")
P = ParamSpec("P")

ATTR = "__synclock__"
LOCKS: dict[str, Lock] = {}
FUNCTIONS: WeakKeyDictionary[Callable[..., Any], Callable[..., Any]] = WeakKeyDictionary()

@overload
def synclock(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Applies lock synchronization to a range of functions or methods.
    Functions sharing the same synclock name, will share the same underlying lock.

    Args:
        name (str): The name of the range which shares the same lock.

    Returns:
        Callable[[Callable[P, R]], Callable[P, R]]: Returns a function wrapper.
    """
    ...
@overload
def synclock(fn: Callable[P, R]) -> Callable[P, R]:
    """Applies lock synchronization to a single function or method.

    Args:
        fn (Callable[P, R]): The function which is wrapped.

    Returns:
        Callable[P, R]: Returns a wrapped function.
    """
    ...
def synclock(x: str | Callable[P, R]) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]: # pyright: ignore[reportInconsistentOverload]

    if isinstance(x, str):
        if x in LOCKS:
            lock = LOCKS[x]
        else:
            lock = Lock()
            LOCKS[x] = lock
    else:
        lock = Lock()


    def wrapper(fn: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with lock:
                return fn(*args, **kwargs)
        return wrapper


    def wrap(fn: Callable[P, R]) -> Callable[P, R]:
        if fn not in FUNCTIONS:
            if hasattr(fn, ATTR):
                raise Exception("Cannot apply synclock to a function twice")

            wrapped = wrapper(fn)
            setattr(wrapped, ATTR, True)
            FUNCTIONS[fn] = wrapped

        return FUNCTIONS[fn]


    if callable(x):
        return wrap(x)
    else:
        return wrap
