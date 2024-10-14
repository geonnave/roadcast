# log_setup.py

import logging
import os
import time

# use readable date as run id, and make an output folder for it
THIS_RUN_ID = f"run-{time.strftime('%Y-%m-%d.%H:%M:%S')}"
OUTPUT_DIR = f"./output-{THIS_RUN_ID}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_logging():
    # Set up the logging configuration
    log_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create a handler for logging to a file
    file_handler = logging.FileHandler(os.path.join(OUTPUT_DIR, 'app.log'))
    file_handler.setFormatter(log_formatter)

    # Create a handler for logging to stdout (console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # Get the root logger and set the log level
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Suppress debug logs from external libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
