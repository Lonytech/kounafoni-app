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


#
# import gzip
# from pathlib import Path
#
# # Path to the mounted volume (e.g., /mnt/gcs)
# volume_mount_path = Path('/mnt/gcs')
#
# # Output folder for decompressed files
# output_folder = Path('/mnt/gcs_decompressed')
#
#
#
#
# # Function to decompress a single GZIP file
# def decompress_gzip(input_file: Path, output_file: Path):
#     with gzip.open(input_file, 'rt') as gz_file:
#         content = gz_file.read()
#
#     # Write the decompressed content to the output file
#     with output_file.open('w') as out_file:
#         out_file.write(content)
#
#
# # Function to iterate over all files in the mounted volume and decompress GZIP files
# def decompress_all_files(volume_path: Path, output_dir: Path):
#     # Create the output folder if it doesn't exist
#     output_folder.mkdir(parents=True, exist_ok=True)
#
#     for file_path in volume_path.rglob('*'):  # rglob('*') to recursively find all files
#         if file_path.is_file():  # If it's a file
#             # Calculate the output path for the decompressed file
#             relative_path = file_path.relative_to(volume_path)
#             output_file_path = output_dir / relative_path.with_suffix('')  # Remove .gz extension
#
#             # Check if the decompressed file already exists
#             if output_file_path.exists():
#                 print(f"File already decompressed, skipping: {output_file_path}")
#                 continue
#
#             # Create parent directories for the output file if they don't exist
#             output_file_path.parent.mkdir(parents=True, exist_ok=True)
#
#             # Decompress the GZIP file
#             try:
#                 decompress_gzip(file_path, output_file_path)
#                 print(f"Decompressed: {file_path} -> {output_file_path}")
#             except Exception as e:
#                 print(f"Error decompressing {file_path}: {e}")
#
#
# # Call the function to decompress all files
# decompress_all_files(volume_mount_path, output_folder)
