"""
Utils function used throughout the project!
"""

import time
from functools import wraps

from dateutil.relativedelta import relativedelta


def human_readable_time(delta):
    """
    Converts a timedelta to a human-readable list of strings.
    :param delta:
    :return:
    """
    attrs = ["years", "months", "days", "hours", "minutes", "seconds"]
    return [
        "%d %s"
        % (
            getattr(delta, attr),
            attr if getattr(delta, attr) > 1 else attr[:-1],
        )
        for attr in attrs
        if getattr(delta, attr)
    ]


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
        elapsed_time = human_readable_time(relativedelta(seconds=int(end - start)))
        print(f"{func.__name__} took {', '.join(elapsed_time)} to execute")
        return result

    return time_wrapper


def format_docs(docs):
    """
    Simple Doc formatter for langchain template
    :param docs:
    :return:
    """
    return "\n\n".join([d.page_content for d in docs])
