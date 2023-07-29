__version__ = "0.0.6"

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from .dtproject import DTProject
