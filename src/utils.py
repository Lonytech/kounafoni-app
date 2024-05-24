"""
Utils function used throughout the project!
"""


def format_docs(docs):
    """
    Simple Doc formatter for langchain template
    :param docs:
    :return:
    """
    return "\n\n".join([d.page_content for d in docs])
