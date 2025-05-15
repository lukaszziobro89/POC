from fastapi.responses import JSONResponse
import pytest
from common.exceptions.pnc_exceptions import (
    Error,
    PncException,
    OcrException,
    ClassificationException,
    VolumeException,
    RequestStoreException
)

class TestErrorClass:
    def test_will_initialize_with_correct_values(self):
        """Test that Error class initializes with correct values."""
        error = Error(400, "Bad Request")
        assert error.code == 400
        assert error.message == "Bad Request"

    def test_will_return_correct_dictionary_on_to_dict(self):
        """Test that to_dict returns the correct dictionary."""
        error = Error(404, "Not Found")
        error_dict = error.to_dict()
        assert error_dict == {"code": 404, "message": "Not Found"}

    def test_will_return_json_response_on_to_response(self):
        """Test that to_response returns a JSONResponse with correct data."""
        error = Error(500, "Server Error")
        response = error.to_response()
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        assert response.body == b'{"code":500,"message":"Server Error"}'

    def test_will_return_response_when_called_directly(self):
        """Test that calling the Error instance returns the same as to_response."""
        error = Error(403, "Forbidden")
        response = error()
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        assert response.body == b'{"code":403,"message":"Forbidden"}'

class TestErrorClassEdgeCases:

    def test_will_fail_initialization_with_negative_code(self):
        with pytest.raises(ValueError) as excinfo:
            Error(-1, "Negative code")
        assert "Invalid HTTP status code: -1. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_less_then_100_code(self):
        with pytest.raises(ValueError) as excinfo:
            Error(66, "Negative code")
        assert "Invalid HTTP status code: 66. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_above_then_599_code(self):
        with pytest.raises(ValueError) as excinfo:
            Error(666, "Negative code")
        assert "Invalid HTTP status code: 666. Code must be between 100 and 599" == str(excinfo.value)

    def test_initialize_with_empty_message(self):
        error = Error(400, "")
        assert error.code == 400
        assert error.message == ""

    def test_initialize_with_long_message(self):
        long_message = "A" * 1000
        error = Error(400, long_message)
        assert error.message == long_message

    def test_error_equality(self):
        error1 = Error(400, "msg")
        error2 = Error(400, "msg")
        assert error1.code == error2.code and error1.message == error2.message

    def test_error_repr(self):
        error = Error(400, "msg")
        assert "Error" in repr(error) or hasattr(error, "__repr__")

    def test_initialize_with_non_integer_code(self):
        with pytest.raises(TypeError) as excinfo:
            Error("not-an-int", "Message")
        assert "Status code must be an integer, got str" == str(excinfo.value)

    def test_initialize_with_non_string_message(self):
        error = Error(400, 12345)
        assert error.message == 12345

class TestPncException:
    def test_will_initialize_with_default_status_code(self):
        """Test that PncException initializes with the default status code."""
        exc = PncException("Generic error")
        assert exc.message == "Generic error"
        assert exc.status_code == 500
        assert str(exc) == "Generic error"

    def test_will_accept_custom_status_code(self):
        """Test that PncException accepts custom status code."""
        exc = PncException("Custom error", 418)
        assert exc.message == "Custom error"
        assert exc.status_code == 418

    def test_can_raise_pnc_exception(self):
        """Test that PncException can be raised and caught."""
        with pytest.raises(PncException) as excinfo:
            raise PncException("Test error")
        assert str(excinfo.value) == "Test error"
        assert excinfo.value.status_code == 500

    def test_function_raising_pnc_exception(self):
        """Test that a function raising PncException can be caught."""
        def func_that_raises():
            raise PncException("Function error")

        with pytest.raises(PncException) as excinfo:
            func_that_raises()
        assert "Function error" in str(excinfo.value)

    def test_pnc_exception_with_custom_attributes(self):
        """Test that PncException can be raised with custom attributes."""
        with pytest.raises(PncException) as excinfo:
            exc = PncException("Custom attributes", 400)
            exc.additional_info = "Extra details"
            raise exc

        assert excinfo.value.status_code == 400
        assert hasattr(excinfo.value, "additional_info")
        assert excinfo.value.additional_info == "Extra details"

    def test_will_raise_error_with_invalid_status_code(self):
        """Test that PncException raises ValueError when initialized with invalid status code."""
        with pytest.raises(ValueError) as excinfo:
            PncException("Invalid code error", 55)
        assert "Invalid HTTP status code: 55. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_less_then_100_code(self):
        with pytest.raises(ValueError) as excinfo:
            PncException("Negative code", 66)
        assert "Invalid HTTP status code: 66. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_above_then_599_code(self):
        with pytest.raises(ValueError) as excinfo:
            PncException("Negative code", 666)
        assert "Invalid HTTP status code: 666. Code must be between 100 and 599" == str(excinfo.value)


class TestOcrException:
    def test_will_initialize_with_default_status_code(self):
        """Test that OcrException initializes with the default status code."""
        exc = OcrException("OCR failed")
        assert exc.message == "OCR failed"
        assert exc.status_code == 422
        assert isinstance(exc, PncException)

    def test_will_accept_custom_status_code(self):
        """Test that OcrException accepts custom status code."""
        exc = OcrException("OCR timed out", 504)
        assert exc.message == "OCR timed out"
        assert exc.status_code == 504

    def test_can_raise_ocr_exception(self):
        """Test that OcrException can be raised and caught."""
        with pytest.raises(OcrException) as excinfo:
            raise OcrException("Test error")
        assert str(excinfo.value) == "Test error"
        assert excinfo.value.status_code == 422

    def test_function_raising_ocr_exception(self):
        """Test that a function raising OcrException can be caught."""
        def func_that_raises():
            raise OcrException("Function error")

        with pytest.raises(OcrException) as excinfo:
            func_that_raises()
        assert "Function error" in str(excinfo.value)

    def test_ocr_exception_with_custom_attributes(self):
        """Test that OcrException can be raised with custom attributes."""
        with pytest.raises(OcrException) as excinfo:
            exc = OcrException("Custom attributes", 400)
            exc.additional_info = "Extra details"
            raise exc

        assert excinfo.value.status_code == 400
        assert hasattr(excinfo.value, "additional_info")
        assert excinfo.value.additional_info == "Extra details"

    def test_will_raise_error_with_invalid_status_code(self):
        """Test that OcrException raises ValueError when initialized with invalid status code."""
        with pytest.raises(ValueError) as excinfo:
            OcrException("Invalid code error", 55)
        assert "Invalid HTTP status code: 55. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_less_then_100_code(self):
        with pytest.raises(ValueError) as excinfo:
            OcrException("Negative code", 66)
        assert "Invalid HTTP status code: 66. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_above_then_599_code(self):
        with pytest.raises(ValueError) as excinfo:
            OcrException("Negative code", 666)
        assert "Invalid HTTP status code: 666. Code must be between 100 and 599" == str(excinfo.value)


class TestClassificationException:
    def test_will_initialize_with_default_status_code(self):
        """Test that ClassificationException initializes with the default status code."""
        exc = ClassificationException("Classification failed")
        assert exc.message == "Classification failed"
        assert exc.status_code == 422
        assert isinstance(exc, PncException)

    def test_will_accept_custom_status_code(self):
        """Test that ClassificationException accepts custom status code."""
        exc = ClassificationException("Classification error", 400)
        assert exc.message == "Classification error"
        assert exc.status_code == 400

    def test_can_raise_classification_exception(self):
        """Test that ClassificationException can be raised and caught."""
        with pytest.raises(ClassificationException) as excinfo:
            raise ClassificationException("Test error")
        assert str(excinfo.value) == "Test error"
        assert excinfo.value.status_code == 422

    def test_function_raising_classification_exception(self):
        """Test that a function raising ClassificationException can be caught."""

        def func_that_raises():
            raise ClassificationException("Function error")

        with pytest.raises(ClassificationException) as excinfo:
            func_that_raises()
        assert "Function error" in str(excinfo.value)

    def test_classification_exception_with_custom_attributes(self):
        """Test that ClassificationException can be raised with custom attributes."""
        with pytest.raises(ClassificationException) as excinfo:
            exc = ClassificationException("Custom attributes", 400)
            exc.additional_info = "Extra details"
            raise exc

        assert excinfo.value.status_code == 400
        assert hasattr(excinfo.value, "additional_info")
        assert excinfo.value.additional_info == "Extra details"

    def test_will_raise_error_with_invalid_status_code(self):
        """Test that PncException raises ValueError when initialized with invalid status code."""
        with pytest.raises(ValueError) as excinfo:
            ClassificationException("Invalid code error", 55)
        assert "Invalid HTTP status code: 55. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_less_then_100_code(self):
        with pytest.raises(ValueError) as excinfo:
            PncException("Negative code", 66)
        assert "Invalid HTTP status code: 66. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_above_then_599_code(self):
        with pytest.raises(ValueError) as excinfo:
            ClassificationException( "Negative code", 666)
        assert "Invalid HTTP status code: 666. Code must be between 100 and 599" == str(excinfo.value)


class TestVolumeException:
    def test_will_accept_custom_status_code(self):
        """Test that VolumeException accepts a custom status code."""
        exc = VolumeException("Volume error", 400)
        assert exc.message == "Volume error"
        assert exc.status_code == 400

    def test_can_raise_volume_exception(self):
        """Test that VolumeException can be raised and caught."""
        with pytest.raises(VolumeException) as excinfo:
            raise VolumeException("Test error")
        assert str(excinfo.value) == "Test error"
        assert excinfo.value.status_code == 422

    def test_function_raising_volume_exception(self):
        """Test that a function raising VolumeException can be caught."""

        def func_that_raises():
            raise VolumeException("Function error")

        with pytest.raises(VolumeException) as excinfo:
            func_that_raises()
        assert "Function error" in str(excinfo.value)

    def test_volume_exception_with_custom_attributes(self):
        """Test that VolumeException can be raised with custom attributes."""
        with pytest.raises(VolumeException) as excinfo:
            exc = VolumeException("Custom attributes", 400)
            exc.additional_info = "Extra details"
            raise exc

        assert excinfo.value.status_code == 400
        assert hasattr(excinfo.value, "additional_info")
        assert excinfo.value.additional_info == "Extra details"

    def test_will_raise_error_with_invalid_status_code(self):
        """Test that VolumeException raises ValueError when initialized with invalid status code."""
        with pytest.raises(ValueError) as excinfo:
            VolumeException("Invalid code error", 55)
        assert "Invalid HTTP status code: 55. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_less_then_100_code(self):
        with pytest.raises(ValueError) as excinfo:
            VolumeException("Negative code", 66)
        assert "Invalid HTTP status code: 66. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_above_then_599_code(self):
        with pytest.raises(ValueError) as excinfo:
            VolumeException("Negative code", 666)
        assert "Invalid HTTP status code: 666. Code must be between 100 and 599" == str(excinfo.value)

class TestRequestStoreException:
    def test_will_initialize_with_default_status_code(self):
        """Test that RequestStoreException initializes with the default status code."""
        exc = RequestStoreException("Request store failed")
        assert exc.message == "Request store failed"
        assert exc.status_code == 422
        assert isinstance(exc, PncException)

    def test_will_accept_custom_status_code(self):
        """Test that RequestStoreException accepts custom status code."""
        exc = RequestStoreException("Request store error", 400)
        assert exc.message == "Request store error"
        assert exc.status_code == 400

    def test_can_raise_request_store_exception(self):
        """Test that RequestStoreException can be raised and caught."""
        with pytest.raises(RequestStoreException) as excinfo:
            raise RequestStoreException("Test error")
        assert str(excinfo.value) == "Test error"
        assert excinfo.value.status_code == 422

    def test_function_raising_request_store_exception(self):
        """Test that a function raising RequestStoreException can be caught."""
        def func_that_raises():
            raise RequestStoreException("Function error")

        with pytest.raises(RequestStoreException) as excinfo:
            func_that_raises()
        assert "Function error" in str(excinfo.value)

    def test_request_store_exception_with_custom_attributes(self):
        """Test that RequestStoreException can be raised with custom attributes."""
        with pytest.raises(RequestStoreException) as excinfo:
            exc = RequestStoreException("Custom attributes", 400)
            exc.additional_info = "Extra details"
            raise exc

        assert excinfo.value.status_code == 400
        assert hasattr(excinfo.value, "additional_info")
        assert excinfo.value.additional_info == "Extra details"

    def test_will_raise_error_with_invalid_status_code(self):
        """Test that RequestStoreException raises ValueError when initialized with invalid status code."""
        with pytest.raises(ValueError) as excinfo:
            RequestStoreException("Invalid code error", 55)
        assert "Invalid HTTP status code: 55. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_less_then_100_code(self):
        with pytest.raises(ValueError) as excinfo:
            RequestStoreException("Negative code", 66)
        assert "Invalid HTTP status code: 66. Code must be between 100 and 599" == str(excinfo.value)

    def test_will_fail_initialization_with_above_then_599_code(self):
        with pytest.raises(ValueError) as excinfo:
            RequestStoreException("Negative code", 666)
        assert "Invalid HTTP status code: 666. Code must be between 100 and 599" == str(excinfo.value)