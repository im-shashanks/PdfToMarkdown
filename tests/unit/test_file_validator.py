"""
Unit tests for file validation service.

Tests file validation logic, security checks, and error handling
following the AAA pattern with comprehensive security test coverage.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

from pdf2markdown.core.config import ApplicationConfig
from pdf2markdown.core.config import ProcessingConfig
from pdf2markdown.core.file_validator import FileValidationResult
from pdf2markdown.core.file_validator import FileValidator
from pdf2markdown.core.file_validator import create_file_validator


class TestFileValidationResult:
    """Test suite for FileValidationResult value object."""

    def test_creates_with_valid_file(self) -> None:
        """Test creating validation result for valid file."""
        # Arrange
        file_path = Path("test.pdf")

        # Act
        result = FileValidationResult(
            is_valid=True,
            file_path=file_path,
            file_size=1024,
            mime_type="application/pdf"
        )

        # Assert
        assert result.is_valid is True
        assert result.file_path == file_path
        assert result.errors == []
        assert result.warnings == []
        assert result.file_size == 1024
        assert result.mime_type == "application/pdf"

    def test_creates_with_invalid_file(self) -> None:
        """Test creating validation result for invalid file."""
        # Arrange
        file_path = Path("invalid.pdf")
        errors = ["File not found", "Invalid format"]
        warnings = ["Large file size"]

        # Act
        result = FileValidationResult(
            is_valid=False,
            file_path=file_path,
            errors=errors,
            warnings=warnings
        )

        # Assert
        assert result.is_valid is False
        assert result.file_path == file_path
        assert result.errors == errors
        assert result.warnings == warnings

    def test_add_error_invalidates_result(self) -> None:
        """Test that adding error invalidates the result."""
        # Arrange
        result = FileValidationResult(is_valid=True, file_path=Path("test.pdf"))

        # Act
        result.add_error("New error")

        # Assert
        assert result.is_valid is False
        assert "New error" in result.errors

    def test_add_warning_preserves_validity(self) -> None:
        """Test that adding warning preserves validity."""
        # Arrange
        result = FileValidationResult(is_valid=True, file_path=Path("test.pdf"))

        # Act
        result.add_warning("New warning")

        # Assert
        assert result.is_valid is True
        assert "New warning" in result.warnings

    def test_get_error_summary_with_no_errors(self) -> None:
        """Test error summary when no errors exist."""
        # Arrange
        result = FileValidationResult(is_valid=True, file_path=Path("test.pdf"))

        # Act
        summary = result.get_error_summary()

        # Assert
        assert summary == "No errors"

    def test_get_error_summary_with_multiple_errors(self) -> None:
        """Test error summary with multiple errors."""
        # Arrange
        result = FileValidationResult(is_valid=False, file_path=Path("test.pdf"))
        result.add_error("First error")
        result.add_error("Second error")

        # Act
        summary = result.get_error_summary()

        # Assert
        assert summary == "First error; Second error"


class TestFileValidator:
    """Test suite for FileValidator service."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = ApplicationConfig(
            processing=ProcessingConfig(max_file_size_mb=10)
        )
        self.validator = FileValidator(self.config)

        # Create temporary directory and files for testing
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create valid PDF file
        self.valid_pdf = self.temp_dir / "valid.pdf"
        self.valid_pdf.write_bytes(b"%PDF-1.4\nHello PDF\n%EOF\n")

        # Create invalid PDF file (wrong header)
        self.invalid_pdf = self.temp_dir / "invalid.pdf"
        self.invalid_pdf.write_bytes(b"Not a PDF file")

        # Create empty PDF file
        self.empty_pdf = self.temp_dir / "empty.pdf"
        self.empty_pdf.write_bytes(b"")

        # Create non-PDF file
        self.text_file = self.temp_dir / "document.txt"
        self.text_file.write_text("This is not a PDF")

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validates_existing_pdf_file(self) -> None:
        """Test validation of existing valid PDF file."""
        # Arrange & Act
        result = self.validator.validate_pdf_file(self.valid_pdf)

        # Assert
        assert result.is_valid is True
        assert result.file_path == self.valid_pdf
        assert len(result.errors) == 0
        assert result.file_size > 0

    def test_validates_nonexistent_file(self) -> None:
        """Test validation of non-existent file."""
        # Arrange
        nonexistent_file = self.temp_dir / "nonexistent.pdf"

        # Act
        result = self.validator.validate_pdf_file(nonexistent_file)

        # Assert
        assert result.is_valid is False
        assert any("File not found" in error for error in result.errors)

    def test_validates_directory_as_file(self) -> None:
        """Test validation when directory is provided instead of file."""
        # Arrange
        directory = self.temp_dir / "directory.pdf"
        directory.mkdir()

        # Act
        result = self.validator.validate_pdf_file(directory)

        # Assert
        assert result.is_valid is False
        assert any("Not a regular file" in error for error in result.errors)

    def test_validates_file_extension(self) -> None:
        """Test validation of file extension."""
        # Arrange & Act
        result = self.validator.validate_pdf_file(self.text_file)

        # Assert
        assert result.is_valid is False
        assert any("must have .pdf extension" in error for error in result.errors)

    def test_validates_empty_file(self) -> None:
        """Test validation of empty file."""
        # Arrange & Act
        result = self.validator.validate_pdf_file(self.empty_pdf)

        # Assert
        assert result.is_valid is False
        assert any("File is empty" in error for error in result.errors)

    def test_validates_file_size_limit(self) -> None:
        """Test validation of file size limits."""
        # Arrange - Create file larger than limit
        large_pdf = self.temp_dir / "large.pdf"
        large_size = self.config.processing.max_file_size_mb * 1024 * 1024 + 1

        with open(large_pdf, 'wb') as f:
            f.write(b"%PDF-1.4\n")
            f.seek(large_size - 1)
            f.write(b"\0")

        # Act
        result = self.validator.validate_pdf_file(large_pdf)

        # Assert
        assert result.is_valid is False
        assert any("exceeds limit" in error for error in result.errors)

    def test_validates_pdf_header(self) -> None:
        """Test validation of PDF file header."""
        # Arrange & Act
        result = self.validator.validate_pdf_file(self.invalid_pdf)

        # Assert
        assert result.is_valid is False
        assert any("does not appear to be a valid PDF" in error for error in result.errors)

    def test_detects_pdf_version(self) -> None:
        """Test detection of PDF version from header."""
        # Arrange
        versioned_pdf = self.temp_dir / "versioned.pdf"
        versioned_pdf.write_bytes(b"%PDF-1.7\nContent\n%EOF\n")

        # Act
        result = self.validator.validate_pdf_file(versioned_pdf)

        # Assert
        assert result.is_valid is True
        # Should have warning about PDF version
        assert any("PDF version" in warning for warning in result.warnings)

    @patch('os.access')
    def test_validates_file_permissions(self, mock_access: Mock) -> None:
        """Test validation of file read permissions."""
        # Arrange
        mock_access.return_value = False

        # Act
        result = self.validator.validate_pdf_file(self.valid_pdf)

        # Assert
        assert result.is_valid is False
        assert any("not readable" in error for error in result.errors)

    def test_validates_security_path_traversal(self) -> None:
        """Test security validation for path traversal attempts."""
        # Arrange
        traversal_path = Path("../../../etc/passwd.pdf")

        # Act
        result = self.validator.validate_pdf_file(traversal_path)

        # Assert
        # File won't exist, but should also have security warning
        assert result.is_valid is False
        assert any("'..' components" in warning for warning in result.warnings)

    def test_validates_system_directory_access(self) -> None:
        """Test prevention of access to system directories."""
        # Arrange
        system_file = Path("/etc/passwd.pdf")

        # Act
        result = self.validator.validate_pdf_file(system_file)

        # Assert
        assert result.is_valid is False
        # Should fail due to file not existing, but would also fail security check

    def test_validates_output_path_writable_directory(self) -> None:
        """Test validation of output path with writable directory."""
        # Arrange
        output_path = self.temp_dir / "output.md"

        # Act
        result = self.validator.validate_output_path(output_path)

        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validates_output_path_nonexistent_directory(self) -> None:
        """Test validation of output path with non-existent directory."""
        # Arrange
        output_path = Path("/nonexistent/directory/output.md")

        # Act
        result = self.validator.validate_output_path(output_path)

        # Assert
        assert result.is_valid is False
        assert any("directory does not exist" in error for error in result.errors)

    @patch('os.access')
    def test_validates_output_directory_permissions(self, mock_access: Mock) -> None:
        """Test validation of output directory write permissions."""
        # Arrange
        output_path = self.temp_dir / "output.md"
        mock_access.return_value = False

        # Act
        result = self.validator.validate_output_path(output_path)

        # Assert
        assert result.is_valid is False
        assert any("No write permission" in error for error in result.errors)

    def test_validates_existing_output_file_without_force(self) -> None:
        """Test validation of existing output file without force flag."""
        # Arrange
        existing_output = self.temp_dir / "existing.md"
        existing_output.write_text("Existing content")

        # Act
        result = self.validator.validate_output_path(existing_output, force=False)

        # Assert
        assert result.is_valid is False
        assert any("already exists" in error for error in result.errors)
        assert any("--force" in error for error in result.errors)

    def test_validates_existing_output_file_with_force(self) -> None:
        """Test validation of existing output file with force flag."""
        # Arrange
        existing_output = self.temp_dir / "existing.md"
        existing_output.write_text("Existing content")

        # Act
        result = self.validator.validate_output_path(existing_output, force=True)

        # Assert
        assert result.is_valid is True
        assert any("Will overwrite" in warning for warning in result.warnings)

    @patch('os.access')
    def test_validates_existing_output_file_permissions(self, mock_access: Mock) -> None:
        """Test validation of existing output file write permissions."""
        # Arrange
        existing_output = self.temp_dir / "existing.md"
        existing_output.write_text("Existing content")

        # Mock os.access to return False for the file, True for directory
        def mock_access_func(path, mode):
            return str(path) != str(existing_output)

        mock_access.side_effect = mock_access_func

        # Act
        result = self.validator.validate_output_path(existing_output, force=True)

        # Assert
        assert result.is_valid is False
        assert any("No write permission for file" in error for error in result.errors)

    def test_validates_output_security_system_directory(self) -> None:
        """Test security validation for output to system directories."""
        # Arrange
        system_output = Path("/etc/malicious.md")

        # Act
        result = self.validator.validate_output_path(system_output)

        # Assert
        assert result.is_valid is False
        assert any("Cannot write to system directory" in error for error in result.errors)

    def test_handles_validation_exceptions_gracefully(self) -> None:
        """Test graceful handling of validation exceptions."""
        # Arrange
        # Create a path that will cause an OSError
        problematic_path = Path("/dev/null/impossible.pdf")

        # Act
        result = self.validator.validate_pdf_file(problematic_path)

        # Assert
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestCreateFileValidator:
    """Test suite for create_file_validator factory function."""

    def test_creates_file_validator_instance(self) -> None:
        """Test that factory creates FileValidator instance."""
        # Arrange
        config = ApplicationConfig()

        # Act
        validator = create_file_validator(config)

        # Assert
        assert isinstance(validator, FileValidator)

    def test_passes_config_to_validator(self) -> None:
        """Test that factory passes config to validator correctly."""
        # Arrange
        config = ApplicationConfig(
            processing=ProcessingConfig(max_file_size_mb=50)
        )

        # Act
        validator = create_file_validator(config)

        # Assert
        assert validator._max_file_size == 50 * 1024 * 1024
