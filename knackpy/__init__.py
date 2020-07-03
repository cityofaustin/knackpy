from .app import App  # noqa: F401
from .api import get, get_metadata, record  # noqa: F401

# Set default logging handler to avoid "No handler found" warnings.
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
