"""
Utils function used throughout the project!
"""

import time
from functools import wraps


def timeit(func):
    """
    Decorator that prints the execution time of a function
    :param func:
    :return:
    """

    @wraps(func)
    def time_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end-start:.2f} seconds to execute")
        return result

    return time_wrapper


def format_docs(docs):
    """
    Simple Doc formatter for langchain template
    :param docs:
    :return:
    """
    return "\n\n".join([d.page_content for d in docs])
