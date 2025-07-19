"""
Unit tests for core exception classes.

Tests the exception hierarchy and error handling functionality
following the AAA (Arrange, Act, Assert) pattern.
"""

from pdf2markdown.core.exceptions import ConfigurationError
from pdf2markdown.core.exceptions import FileSystemError
from pdf2markdown.core.exceptions import InvalidPdfError
from pdf2markdown.core.exceptions import PdfToMarkdownError
from pdf2markdown.core.exceptions import ProcessingError
from pdf2markdown.core.exceptions import ValidationError


class TestPdfToMarkdownError:
    """Test suite for base PdfToMarkdownError class."""

    def test_creates_error_with_message_only(self) -> None:
        """Test creating error with just a message."""
        # Arrange
        message = "Test error message"

        # Act
        error = PdfToMarkdownError(message)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "PdfToMarkdownError"
        assert error.details == {}

    def test_creates_error_with_all_parameters(self) -> None:
        """Test creating error with all parameters."""
        # Arrange
        message = "Test error"
        error_code = "TEST_ERROR"
        details = {"key": "value", "number": 42}

        # Act
        error = PdfToMarkdownError(message, error_code, details)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == error_code
        assert error.details == details

    def test_inherits_from_exception(self) -> None:
        """Test that PdfToMarkdownError inherits from Exception."""
        # Arrange & Act
        error = PdfToMarkdownError("test")

        # Assert
        assert isinstance(error, Exception)


class TestValidationError:
    """Test suite for ValidationError class."""

    def test_creates_validation_error_with_message(self) -> None:
        """Test creating validation error with message only."""
        # Arrange
        message = "Validation failed"

        # Act
        error = ValidationError(message)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details == {}

    def test_creates_validation_error_with_field(self) -> None:
        """Test creating validation error with field information."""
        # Arrange
        message = "Invalid value"
        field = "email"

        # Act
        error = ValidationError(message, field)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details == {"field": field}

    def test_inherits_from_pdf_to_markdown_error(self) -> None:
        """Test inheritance hierarchy."""
        # Arrange & Act
        error = ValidationError("test")

        # Assert
        assert isinstance(error, PdfToMarkdownError)
        assert isinstance(error, Exception)


class TestInvalidPdfError:
    """Test suite for InvalidPdfError class."""

    def test_creates_pdf_error_with_message(self) -> None:
        """Test creating PDF error with message only."""
        # Arrange
        message = "Invalid PDF file"

        # Act
        error = InvalidPdfError(message)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "INVALID_PDF"
        assert error.details == {}

    def test_creates_pdf_error_with_file_path(self) -> None:
        """Test creating PDF error with file path."""
        # Arrange
        message = "Corrupted PDF"
        file_path = "/path/to/file.pdf"

        # Act
        error = InvalidPdfError(message, file_path)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "INVALID_PDF"
        assert error.details == {"file_path": file_path}


class TestProcessingError:
    """Test suite for ProcessingError class."""

    def test_creates_processing_error_with_message(self) -> None:
        """Test creating processing error with message only."""
        # Arrange
        message = "Processing failed"

        # Act
        error = ProcessingError(message)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "PROCESSING_ERROR"
        assert error.details == {}

    def test_creates_processing_error_with_stage_and_file(self) -> None:
        """Test creating processing error with stage and file information."""
        # Arrange
        message = "Failed at parsing stage"
        stage = "text_extraction"
        file_path = "/path/to/document.pdf"

        # Act
        error = ProcessingError(message, stage, file_path)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "PROCESSING_ERROR"
        assert error.details == {"stage": stage, "file_path": file_path}


class TestFileSystemError:
    """Test suite for FileSystemError class."""

    def test_creates_filesystem_error_with_message(self) -> None:
        """Test creating filesystem error with message only."""
        # Arrange
        message = "File not found"

        # Act
        error = FileSystemError(message)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "FILESYSTEM_ERROR"
        assert error.details == {}

    def test_creates_filesystem_error_with_operation_and_file(self) -> None:
        """Test creating filesystem error with operation details."""
        # Arrange
        message = "Read operation failed"
        operation = "read"
        file_path = "/path/to/file.pdf"

        # Act
        error = FileSystemError(message, operation, file_path)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "FILESYSTEM_ERROR"
        assert error.details == {"operation": operation, "file_path": file_path}


class TestConfigurationError:
    """Test suite for ConfigurationError class."""

    def test_creates_configuration_error_with_message(self) -> None:
        """Test creating configuration error with message only."""
        # Arrange
        message = "Invalid configuration"

        # Act
        error = ConfigurationError(message)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details == {}

    def test_creates_configuration_error_with_config_key(self) -> None:
        """Test creating configuration error with config key."""
        # Arrange
        message = "Missing required setting"
        config_key = "api_key"

        # Act
        error = ConfigurationError(message, config_key)

        # Assert
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details == {"config_key": config_key}
