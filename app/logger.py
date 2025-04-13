"""
This is the logger for FASTAPI application.
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,  # Adjust as needed (DEBUG, INFO, WARNING, ERROR)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("fastapi_app")