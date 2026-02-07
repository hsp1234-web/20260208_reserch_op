import threading
import time
import functools
from src.exceptions import TimeoutError

def timeout_watchdog(seconds=20):
    """
    A decorator that raises a TimeoutError if a function takes longer than `seconds`.
    Note: This uses a separate thread to monitor, so it won't interrupt blocking I/O
    that doesn't release the GIL, but it's better than nothing.
    For heavy I/O, 'requests' timeout is better.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")]

            def target():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)

            if thread.is_alive():
                raise TimeoutError(f"Operation {func.__name__} hung for more than {seconds} seconds")

            if isinstance(res[0], Exception):
                raise res[0]
            return res[0]
        return wrapper
    return decorator
