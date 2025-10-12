
import logging
import logging.config
import json
from pythonjsonlogger import jsonlogger
import os

class JsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom formatter to add extra fields to the JSON log.
    """
    def add_fields(self, log_record, record, message_dict):
        super(JsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['name'] = record.name

def setup_logging(log_path='logs/app.log'):
    """
    Configures the logging for the entire application.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'logging_config.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'json_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': log_path,
                'maxBytes': 10485760, # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'json_file']
        }
    })
