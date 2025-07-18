import logging
import os
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    #load settings
    try:
        import json
        with open('config/settings.json', 'r') as f:
            settings = json.load(f)
            log_level = settings.get('log_level', 'INFO')
    except:
        log_level = 'INFO' #Default if file not found or error in reading
        
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Create a file handler
    log_filename = f"logs/apartment_hunter_{datetime.now().strftime('%d%m%Y')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Return the configured logger
    return logger