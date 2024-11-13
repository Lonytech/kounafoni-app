"""
Utils function used throughout the project!
"""

import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

from dateutil.relativedelta import relativedelta
from langchain_core.documents.base import Document

# any function type
F = TypeVar("F", bound=Callable[..., Any])


def human_readable_time(delta: relativedelta) -> list[str]:
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


def timeit(func: F) -> F:
    """
    Decorator that prints the execution time of a function
    :param func:
    :return:
    """

    @wraps(func)
    def time_wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed_time = human_readable_time(relativedelta(seconds=int(end - start)))
        print(f"{func.__name__} took {', '.join(elapsed_time)} to execute")
        return result

    return time_wrapper  # type: ignore


def format_docs_to_string(docs: list[Document]) -> str:
    """
    Simple Doc formatter for langchain template
    :param docs:
    :return:
    """
    docs_formatted = list()
    for d in docs:
        doc_presentation = f"Doc title : <<{d.metadata['title']}>>\n"
        doc_presentation += f"Doc date : <<{d.metadata['date']}>>\n"
        doc_presentation += f"Doc source_paper : <<{d.metadata['source_paper']}>>\n"
        doc_presentation += f"Doc link : <<{d.metadata['link']}>>\n"
        doc_presentation += f"Doc page_content : <<{d.page_content}>>\n"
        doc_presentation += f"Question time : <<{datetime.now()}>>\n"
        docs_formatted.append(doc_presentation)
    return f"\n\n{'-' * 50}\n".join(docs_formatted)


def format_docs_to_docs(docs: list[Document]) -> list[Document]:
    docs_formatted = list()
    # print(
    #     docs[0].metadata["date"],
    #     type(docs[0].metadata["date"]),
    #     docs[0].metadata.get("date"),
    # )
    # print(docs[:3])

    for d in docs:
        print(
            # d.metadata["date"],
            # type(d.metadata["date"]),
            d.metadata.get("date"),
            d.metadata.get("source_paper"),
            d.page_content,
        )
        doc_presentation = f"Doc title : <<{d.metadata['title']}>>\n"
        doc_presentation += f"Doc date : <<{d.metadata['date']}>>\n"
        doc_presentation += f"Doc source_paper : <<{d.metadata['source_paper']}>>\n"
        doc_presentation += f"Doc link : <<{d.metadata['link']}>>\n"
        doc_presentation += f"Doc page_content : <<{d.page_content}>>\n"
        doc_presentation += f"Question time : <<{datetime.now()}>>\n"

        # saving doc
        d.page_content = doc_presentation
        docs_formatted.append(d)
    return docs_formatted


def get_most_recent_folder(directory_path: Path) -> Path | None:

    # Convert the input to a Path object if it's a string
    base_path = Path(directory_path)

    # Get all directories and filter those that match date format
    # Assuming folders are named in the format "YYYY-MM-DD"
    date_folders = []
    for folder in base_path.iterdir():
        if folder.is_dir():
            try:
                # Try to parse the folder name as a date
                date = datetime.strptime(folder.name, "%Y-%m-%d")
                date_folders.append((date, folder))
            except ValueError:
                # Skip folders that don't match the date format
                continue

    if not date_folders:
        return None

    # Sort by date and get the most recent one
    most_recent = max(date_folders, key=lambda x: x[0])
    return most_recent[1]
