import time

from collections.abc import Callable


def profile(func: Callable) -> Callable:
    """
    Decorator that calculates the time taken to execute a function and prints it.
    """
    
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.2f}s")
        return result

    return wrapper