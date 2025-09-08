"""
Retry utilities for error recovery.
Simple, low-effort retry mechanisms for failed operations.
"""

import asyncio
import functools
from typing import Callable, Any, Union, List, Type
from ..utils.logging import structured_logger


def async_retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
):
    """
    Async retry decorator with exponential backoff.

    Args:
        retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay between retries
        exceptions: Exception type(s) to catch and retry on
    """
    if isinstance(exceptions, type):
        exceptions = [exceptions]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            logger = structured_logger()
            last_exception = None
            current_delay = delay

            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e

                    if attempt < retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{retries + 1} failed for {func.__name__}: {str(e)}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {retries + 1} attempts failed for {func.__name__}: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator


def sync_retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
):
    """
    Synchronous retry decorator with exponential backoff.
    """
    if isinstance(exceptions, type):
        exceptions = [exceptions]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = structured_logger()
            last_exception = None
            current_delay = delay

            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e

                    if attempt < retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{retries + 1} failed for {func.__name__}: {str(e)}"
                        )
                        import time

                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {retries + 1} attempts failed for {func.__name__}: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator
