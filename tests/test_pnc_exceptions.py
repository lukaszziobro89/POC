import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from common.exceptions.handlers import ClassificationException, OcrException, VolumeException, PncException
from common.exceptions.pnc_exceptions import setup_exception_handlers


@pytest.fixture
def test_app():
    """Create a test FastAPI app with exception handlers configured."""
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/test-classification-error")
    async def test_classification_error():
        raise ClassificationException("Classification test error")

    @app.get("/test-ocr-error")
    async def test_ocr_error():
        raise OcrException("OCR test error")

    @app.get("/test-volume-error")
    async def test_volume_error():
        raise VolumeException("Volume test error")

    @app.get("/test-pnc-error")
    async def test_pnc_error():
        raise PncException("PNC test error", 400)

    @app.get("/test-generic-error")
    async def test_generic_error():
        raise ValueError("Generic test error")

    @app.get("/test-custom-status-error")
    async def test_custom_status_error():
        exc = ValueError("Custom status error")
        exc.status_code = 418  # I'm a teapot
        raise exc

    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI app."""
    # Setting raise_server_exceptions=False is crucial for testing exception handlers
    return TestClient(test_app, raise_server_exceptions=False)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing log calls."""
    with patch("common.exceptions.pnc_exceptions.logger") as mock:
        yield mock


class TestExceptionHandlers:
    def test_classification_exception_returns_expected_response(self, client):
        """Test that ClassificationException returns the expected response."""
        response = client.get("/test-classification-error")
        assert response.status_code == 422
        assert response.json() == {"code": 422, "message": "Classification test error"}

    def test_ocr_exception_returns_expected_response(self, client):
        """Test that OcrException returns the expected response."""
        response = client.get("/test-ocr-error")
        assert response.status_code == 422
        assert response.json() == {"code": 422, "message": "OCR test error"}

    def test_volume_exception_returns_expected_response(self, client):
        """Test that VolumeException returns the expected response."""
        response = client.get("/test-volume-error")
        assert response.status_code == 422
        assert response.json() == {"code": 422, "message": "Volume test error"}

    def test_pnc_exception_returns_expected_response(self, client):
        """Test that PncException returns the expected response."""
        response = client.get("/test-pnc-error")
        assert response.status_code == 400
        assert response.json() == {"code": 400, "message": "PNC test error"}

    def test_unhandled_exception_returns_generic_error_response(self, client):
        """Test that unhandled exceptions return a generic error response."""
        response = client.get("/test-generic-error")
        assert response.status_code == 500
        assert response.json() == {"message": "Generic test error"}

    def test_exception_with_status_code_attribute_uses_that_code(self, client):
        """Test that exceptions with a status_code attribute use that code."""
        response = client.get("/test-custom-status-error")
        assert response.status_code == 418
        assert response.json() == {"message": "Custom status error"}

    @patch("common.exceptions.pnc_exceptions.logger")
    def test_classification_exceptions_are_properly_logged(self, mock_logger, client):
        """Test that ClassificationException errors are properly logged."""
        client.get("/test-classification-error")
        mock_logger.error.assert_called()
        # Get the most recent call
        calls = mock_logger.error.call_args_list
        if calls:
            call_args = calls[-1][0]
            call_kwargs = calls[-1][1]

            assert "Request failed" in call_args[0]
            assert call_kwargs.get("error") == "Classification test error"
            assert call_kwargs.get("status_code") == 422
            assert call_kwargs.get("exception_type") == "ClassificationException"

    @patch("common.exceptions.pnc_exceptions.logger")
    def test_ocr_exceptions_are_properly_logged(self, mock_logger, client):
        """Test that OcrException errors are properly logged."""
        client.get("/test-ocr-error")
        mock_logger.error.assert_called()
        calls = mock_logger.error.call_args_list
        if calls:
            call_args = calls[-1][0]
            call_kwargs = calls[-1][1]

            assert "Request failed" in call_args[0]
            assert call_kwargs.get("error") == "OCR test error"
            assert call_kwargs.get("status_code") == 422
            assert call_kwargs.get("exception_type") == "OcrException"

    @patch("common.exceptions.pnc_exceptions.logger")
    def test_volume_exceptions_are_properly_logged(self, mock_logger, client):
        """Test that VolumeException errors are properly logged."""
        client.get("/test-volume-error")
        mock_logger.error.assert_called()
        calls = mock_logger.error.call_args_list
        if calls:
            call_args = calls[-1][0]
            call_kwargs = calls[-1][1]

            assert "Request failed" in call_args[0]
            assert call_kwargs.get("error") == "Volume test error"
            assert call_kwargs.get("status_code") == 422
            assert call_kwargs.get("exception_type") == "VolumeException"

    @patch("common.exceptions.pnc_exceptions.logger")
    def test_pnc_exceptions_are_properly_logged(self, mock_logger, client):
        """Test that PncException errors are properly logged."""
        client.get("/test-pnc-error")
        mock_logger.error.assert_called()
        calls = mock_logger.error.call_args_list
        if calls:
            call_args = calls[-1][0]
            call_kwargs = calls[-1][1]

            assert "Request failed" in call_args[0]
            assert call_kwargs.get("error") == "PNC test error"
            assert call_kwargs.get("status_code") == 400
            assert call_kwargs.get("exception_type") == "PncException"

    @patch("common.exceptions.pnc_exceptions.logger")
    def test_generic_exceptions_are_properly_logged(self, mock_logger, client):
        """Test that generic exceptions are properly logged."""
        client.get("/test-generic-error")
        mock_logger.error.assert_called()
        # Get the most recent call
        calls = mock_logger.error.call_args_list
        if calls:
            call_args = calls[-1][0]
            call_kwargs = calls[-1][1]

            assert "Request failed" in call_args[0]
            assert call_kwargs.get("error") == "Generic test error"
            assert call_kwargs.get("status_code") == 500
            assert call_kwargs.get("exception_type") == "ValueError"

    def test_request_state_logger_is_used_when_present(self, test_app):
        """Test that request.state.logger is used if present."""
        custom_logger = MagicMock()

        with patch("common.exceptions.pnc_exceptions.logger") as default_logger:
            # Set up middleware to add custom logger to request state
            @test_app.middleware("http")
            async def add_logger_to_request(request: Request, call_next):
                request.state.logger = custom_logger
                return await call_next(request)

            client = TestClient(test_app, raise_server_exceptions=False)
            client.get("/test-classification-error")

            # Verify the custom logger was used instead of the default
            custom_logger.error.assert_called()
            default_logger.error.assert_not_called()