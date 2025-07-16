import os
import sys
from typing import Final

from loguru import logger

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGURU_LEVEL}])

__version__ = "0.1.0"
