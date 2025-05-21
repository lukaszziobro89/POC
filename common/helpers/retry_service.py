import time
import logging
import asyncio
from functools import wraps
from typing import Type, Union, List, Callable, Optional, Any


def retry(
        max_tries: int = 3,
        delay_seconds: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions_to_check: Union[Type[Exception], List[Type[Exception]]] = Exception,
        logger_provider: Optional[Callable] = None,
):
    """
    A decorator that automatically retries a function when specified exceptions occur.

    Works with both synchronous and asynchronous functions and supports exponential backoff.
    Compatible with FastAPI's dependency injection for logging.

    Example usage:
        # Basic usage with async function
        @retry(max_tries=3, exceptions_to_check=[ValueError, ConnectionError])
        async def fetch_data():
            # code that might fail

        # With FastAPI dependency injection for logging
        @retry(logger_provider=Depends(get_logger_with_context))
        def process_data():
            # code that might fail

    Args:
        max_tries: Maximum number of attempts before giving up (default: 3)
        delay_seconds: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
                        e.g., 1s, 2s, 4s with factor=2.0
        exceptions_to_check: Which exception(s) should trigger a retry
                            (default: all Exceptions)
        logger_provider: Optional FastAPI dependency to inject a logger
                        e.g., Depends(get_logger_with_context)

    Returns:
        The result of the decorated function upon success

    Raises:
        The last exception caught if all retry attempts fail
    """
    # Ensure exceptions_to_check is always a list for consistent handling
    if not isinstance(exceptions_to_check, list):
        exceptions_to_check = [exceptions_to_check]

    def decorator(func):
        """Create the appropriate retry wrapper based on the decorated function type"""
        # Determine if the function is async or sync
        is_async = asyncio.iscoroutinefunction(func)

        def _get_logger(kwargs, module_name):
            """Extract logger from kwargs or create a default one"""
            # Check if logger was explicitly passed
            logger = kwargs.get('logger')

            # If no logger found, create default logger
            if logger is None:
                logger = logging.getLogger(module_name)

            return logger

        def _log_retry_attempt(logger, attempt, func_name, exception, wait_time):
            """Log a retry attempt in a standardized format"""
            logger.warning(
                f"Attempt {attempt}/{max_tries} for '{func_name}' "
                f"failed with {exception.__class__.__name__}: {exception}. "
                f"Retrying in {wait_time:.2f}s..."
            )

        def _log_retry_failure(logger, func_name, exception):
            """Log the final failure after all retry attempts"""
            logger.error(
                f"All {max_tries} attempts for '{func_name}' "
                f"failed with {exception.__class__.__name__}: {exception}."
            )

        async def _retry_function(*args, **kwargs):
            """Retry logic for async functions"""
            logger = _get_logger(kwargs, func.__module__)
            last_exception = None

            for attempt in range(1, max_tries + 1):
                try:
                    if is_async:
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except tuple(exceptions_to_check) as exc:
                    last_exception = exc

                    if attempt < max_tries:
                        wait_time = delay_seconds * (backoff_factor ** (attempt - 1))
                        _log_retry_attempt(logger, attempt, func.__name__, exc, wait_time)
                        if is_async:
                            await asyncio.sleep(wait_time)
                        else:
                            time.sleep(wait_time)
                    else:
                        _log_retry_failure(logger, func.__name__, exc)

            raise last_exception

        # Choose the appropriate wrapper: async/sync with/without logger
        if is_async:
            if logger_provider:
                @wraps(func)
                async def wrapper(*args, logger=logger_provider, **kwargs):
                    return await _retry_function(*args, logger=logger, **kwargs)
            else:
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    return await _retry_function(*args, **kwargs)
        else:
            if logger_provider:
                @wraps(func)
                def wrapper(*args, logger=logger_provider, **kwargs):
                    return _retry_function(*args, logger=logger, **kwargs)
            else:
                @wraps(func)
                def wrapper(*args, **kwargs):
                    return _retry_function(*args, **kwargs)

        return wrapper

    return decorator