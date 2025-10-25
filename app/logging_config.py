import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    """
    Configures JSON logging for the application.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)