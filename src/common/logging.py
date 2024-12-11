import logging

from logging import Logger

def get_logger() -> Logger:
    """Generates a basic Logger

    Returns:
        Logger: _description_
    """
    return logging.getLogger(__name__)