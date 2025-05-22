import asyncio

import pytest
import logging
from unittest.mock import MagicMock, patch, call, AsyncMock

from common.helpers.retry_service import retry

class RetryTestException(Exception):
    pass

class AnotherRetryTestException(Exception):
    pass


# ====== Synchronous Function Tests ======

@pytest.mark.asyncio  # All tests need to be async because _retry_function is async
async def test_sync_function_succeeds_first_try():
    """Test that a sync function that succeeds on first try works normally."""
    mock_func = MagicMock(return_value="success")

    @retry()
    def test_func(logger=None):
        return mock_func()

    result = await test_func(logger=None)

    assert result == "success"
    mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_sync_function_retries_and_succeeds():
    """Test that a sync function retries after exceptions and eventually succeeds."""
    mock_func = MagicMock(side_effect=[RetryTestException("Error 1"), RetryTestException("Error 2"), "success"])

    @retry(max_tries=3, delay_seconds=0.01)
    def test_func(logger=None):
        return mock_func()

    result = await test_func(logger=None)

    assert result == "success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_sync_function_retries_and_fails():
    """Test that a sync function gives up after max retries and raises the last exception."""
    mock_func = MagicMock(side_effect=RetryTestException("Persistent error"))

    @retry(max_tries=3, delay_seconds=0.01)
    def test_func(logger=None):
        return mock_func()

    with pytest.raises(RetryTestException, match="Persistent error"):
        await test_func(logger=None)

    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_sync_function_specific_exception():
    """Test that retry only happens for specified exception types."""
    mock_func = MagicMock(side_effect=[RetryTestException("Retry this"), AnotherRetryTestException("Don't retry this")])

    @retry(max_tries=3, delay_seconds=0.01, exceptions_to_check=RetryTestException)
    def test_func(logger=None):
        return mock_func()

    with pytest.raises(AnotherRetryTestException, match="Don't retry this"):
        await test_func(logger=None)

    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_sync_function_backoff():
    """Test that the backoff timing works correctly."""
    mock_func = MagicMock(side_effect=[RetryTestException("Error 1"), RetryTestException("Error 2"), "success"])

    with patch('time.sleep') as mock_sleep:
        @retry(max_tries=3, delay_seconds=1.0, backoff_factor=2.0)
        def test_func():
            return mock_func()

        result = await test_func()

    assert mock_sleep.call_count == 2
    mock_sleep.assert_has_calls([call(1.0), call(2.0)])
    assert result == "success"


# ====== Asynchronous Function Tests ======

@pytest.mark.asyncio
async def test_async_function_succeeds_first_try():
    """Test that an async function that succeeds on first try works normally."""
    mock_func = MagicMock()
    mock_func.return_value = "success"

    @retry()
    async def test_func(logger=None):
        return mock_func()

    result = await test_func(logger=None)

    assert result == "success"
    mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_async_function_retries_and_succeeds():
    """Test that an async function retries after exceptions and eventually succeeds."""
    mock_coro1 = MagicMock()
    mock_coro1.side_effect = RetryTestException("Error 1")
    mock_coro2 = MagicMock()
    mock_coro2.side_effect = RetryTestException("Error 2")
    mock_coro3 = MagicMock()
    mock_coro3.return_value = "success"

    mock_func = MagicMock(side_effect=[mock_coro1, mock_coro2, mock_coro3])

    @retry(max_tries=3, delay_seconds=0.01)
    async def test_func(logger=None):
        return mock_func()()

    result = await test_func(logger=None)

    assert result == "success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_async_function_retries_and_fails():
    """Test that an async function gives up after max retries and raises the last exception."""
    mock_coro = MagicMock()
    mock_coro.side_effect = RetryTestException("Persistent error")
    mock_func = MagicMock(return_value=mock_coro)

    @retry(max_tries=3, delay_seconds=0.01)
    async def test_func(logger=None):
        return mock_func()()

    with pytest.raises(RetryTestException, match="Persistent error"):
        await test_func(logger=None)

    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_async_function_backoff():
    """Test that the backoff timing works correctly for async functions."""
    mock_func = MagicMock(side_effect=[RetryTestException("Error 1"), RetryTestException("Error 2"), "success"])

    with patch('asyncio.sleep') as mock_sleep:
        @retry(max_tries=3, delay_seconds=1.0, backoff_factor=2.0)
        async def test_func(logger=None):
            return mock_func()

        result = await test_func(logger=None)

    assert mock_sleep.call_count == 2
    mock_sleep.assert_has_calls([call(1.0), call(2.0)])
    assert result == "success"


# ====== Logger Tests ======

@pytest.mark.asyncio
async def test_logger_is_used():
    """Test that the logger is correctly used to log retry attempts."""
    mock_func = MagicMock(side_effect=[RetryTestException("Error 1"), "success"])
    mock_logger = MagicMock(spec=logging.Logger)

    @retry(max_tries=3, delay_seconds=0.01)
    def test_func(logger=None):
        return mock_func()

    result = await test_func(logger=mock_logger)

    assert result == "success"
    assert mock_logger.warning.call_count == 1
    assert mock_logger.error.call_count == 0


@pytest.mark.asyncio
async def test_async_wrapper_with_logger_provider():
    # Arrange
    mock_func = AsyncMock(return_value="ok")
    mock_logger = MagicMock()

    # Patch logger_provider to return mock_logger
    def logger_provider():
        return mock_logger

    # Decorate the async function with retry and logger_provider
    decorated = retry(logger_provider=logger_provider)(mock_func)

    # Act
    result = await decorated()

    # Assert
    assert result == "ok"
    mock_func.assert_awaited_once()


def test_sync_wrapper_with_logger_provider():
    from common.helpers.retry_service import retry
    from unittest.mock import MagicMock

    mock_func = MagicMock(return_value="ok")
    mock_logger = MagicMock()

    def logger_provider():
        return mock_logger

    decorated = retry(logger_provider=logger_provider)(mock_func)

    # Run the coroutine to completion
    result = asyncio.run(decorated())

    assert result == "ok"
    mock_func.assert_called_once()

@pytest.mark.asyncio
async def test_logger_records_all_failures():
    """Test that the logger records each failed attempt and final failure."""
    mock_func = MagicMock(side_effect=RetryTestException("Persistent error"))
    mock_logger = MagicMock(spec=logging.Logger)

    @retry(max_tries=3, delay_seconds=0.01)
    def test_func(logger=None):
        return mock_func()

    with pytest.raises(RetryTestException):
        await test_func(logger=mock_logger)

    assert mock_logger.warning.call_count == 2
    assert mock_logger.error.call_count == 1
