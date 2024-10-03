import time

from collections.abc import Callable


def profile(func: Callable) -> Callable:
    """
    Decorator to profile a function.
    The functions will return a tuple with the result and the time it took to execute.
    """
    
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, end - start

    return wrapper