import logging
import sys
from typing import Optional

from config import settings


def setup_logger(
    name: str = "coder",
    level: Optional[int] = None
) -> logging.Logger:
    """Set up and return a configured logger"""
    
    logger = logging.getLogger(name)
    
    if level is None:
        level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger


# Default logger instance
logger = setup_logger()
