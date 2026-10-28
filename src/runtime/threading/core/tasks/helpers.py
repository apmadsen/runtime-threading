from collections.abc import Callable
from typing import Any


def get_function_name(fn: Callable[..., Any]) -> str:
    return f"{fn.__module__}.{fn.__name__}" if fn.__module__ else fn.__name__
