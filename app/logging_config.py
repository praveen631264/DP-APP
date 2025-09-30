import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Sets up structured JSON logging for the application."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Use a handler that outputs to stdout
    logHandler = logging.StreamHandler(sys.stdout)

    # Use a JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(funcName)s %(message)s'
    )

    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    # Set the root logger's level to INFO
    logging.basicConfig(level=logging.INFO)
