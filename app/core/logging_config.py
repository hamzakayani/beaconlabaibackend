import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logging():
    # Create a logger
    logger = logging.getLogger("fastapi")
    
    logger.setLevel(logging.INFO)  # Set the default log level
    
    # Create logs directory if it doesn't exist
    log_dir = 'app/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a timed rotating file handler
    log_filename = f'{log_dir}/app_logs_{datetime.now().strftime("%Y%m%d")}.log'
    handler = TimedRotatingFileHandler(
        log_filename,
        when='midnight',  # Rotate at midnight
        interval=1,       # Create new file every day
        backupCount=30    # Keep last 30 days of logs
    )
    handler.setLevel(logging.INFO)
    
    # Create a formatter for structured logging
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(handler)
    logger.propagate = False
    
    # Optionally, log to console (stdout)
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setLevel(logging.INFO)
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)

    return logger
