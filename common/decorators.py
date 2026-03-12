import logging
import time
from functools import wraps

logger = logging.getLogger('contactmailer')

def log_time(func):
    """Decorator to log the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"Function '{func.__name__}' executed in {duration:.4f} seconds.")
        return result
    return wrapper

def safe(func):
    """Decorator to catch exceptions and log them, preventing the crash."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in '{func.__name__}': {str(e)}", exc_info=True)
            return None
    return wrapper
