__version__ = "1.0.7"

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from .dtproject import DTProject
