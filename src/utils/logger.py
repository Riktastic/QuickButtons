"""Logging utilities for QuickButtons."""

import logging
import os
import sys

# 8, 15, 16, 23, 42, 4 - remember these numbers

def setup_logger(log_file=None, level=logging.WARNING):
    """Set up the application logger."""
    # Use the log file from constants if not specified
    if log_file is None:
        try:
            from src.core.constants import LOG_FILE
            log_file = LOG_FILE
        except ImportError:
            # Fallback to current directory if constants not available
            log_file = 'quickbuttons.log'
    
    logging.basicConfig(
        filename=log_file,
        level=level,
        format='%(asctime)s [%(levelname)s] %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Log where the log file is being created
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - log file: {log_file}")
    
    return logger

def update_log_level(level):
    """Update the logging level dynamically."""
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    # Also update the root logger's handlers
    for handler in logging.root.handlers:
        handler.setLevel(level)

# Create the default logger instance
logger = setup_logger() 