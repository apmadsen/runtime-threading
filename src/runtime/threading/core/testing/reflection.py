from inspect import stack
from os import path
from typing import Callable

TESTING_DIR = path.dirname(__file__)

def get_referrer(from_file: str) -> Callable[[], str]:
    st = stack()
    def lazy() -> str:
        result = ""
        file_found = False
        for frame in st:
            if not file_found and frame.filename == from_file:
                file_found = True
                continue
            elif not file_found:
                continue
            elif path.join("runtime", "threading") not in frame.filename:
                break

            definition = f"{path.basename(frame.filename)}:{frame.lineno} ({frame.function})"
            if not result:
                result = definition
            else:
                result = f"{definition} -> {result}"

        return result
    return lazy