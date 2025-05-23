import logging 
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import os

def setup_logger():
    """Configure and return the main application logger."""
    # Create logs directory relative to project root
    log_dir = Path(__file__).parent.parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Main logger configuration
    logger = logging.getLogger('mini_coffee')
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers in env reloads
    if logger.handlers:
        return logger
    
    # Formatting
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s %(module)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Regular app log (rotates daily, keeps 30 days)
    app_handler = TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when='midnight',
        backupCount=30,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    
    # Error log (WARNING+, separate file)
    error_handler = TimedRotatingFileHandler(
        filename=log_dir / "errors.log",
        when='midnight',
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(app_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger