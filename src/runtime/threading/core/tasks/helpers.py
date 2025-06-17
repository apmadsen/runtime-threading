from typing import Callable, Any

def get_function_name(fn: Callable[..., Any]) -> str:
    return f"{fn.__module__}.{fn.__name__}" if fn.__module__ else fn.__name__
