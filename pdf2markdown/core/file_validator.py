"""
File validation service for PdfToMarkdown application.

This module provides comprehensive file validation following security
best practices and the Single Responsibility Principle.
"""

import mimetypes
import os
from pathlib import Path
from typing import List
from typing import Optional

from pdf2markdown.core.config import ApplicationConfig


class FileValidationResult:
    """Result object for file validation operations.
    
    This value object encapsulates validation results with detailed
    information about any issues found.
    """

    def __init__(
        self,
        is_valid: bool,
        file_path: Path,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        file_size: Optional[int] = None,
        mime_type: Optional[str] = None
    ) -> None:
        """Initialize validation result.
        
        Args:
            is_valid: Whether the file passed validation
            file_path: Path to the validated file
            errors: List of validation errors (if any)
            warnings: List of validation warnings (if any)
            file_size: File size in bytes
            mime_type: Detected MIME type
        """
        self.is_valid = is_valid
        self.file_path = file_path
        self.errors = errors or []
        self.warnings = warnings or []
        self.file_size = file_size
        self.mime_type = mime_type

    def add_error(self, error: str) -> None:
        """Add a validation error.
        
        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning.
        
        Args:
            warning: Warning message to add
        """
        self.warnings.append(warning)

    def get_error_summary(self) -> str:
        """Get a summary of all validation errors.
        
        Returns:
            Formatted string with all errors
        """
        if not self.errors:
            return "No errors"
        return "; ".join(self.errors)


class FileValidator:
    """Service for validating PDF files with security considerations.
    
    This service follows the Single Responsibility Principle by focusing
    solely on file validation, including security checks, size limits,
    and format verification.
    """

    def __init__(self, config: ApplicationConfig) -> None:
        """Initialize file validator with configuration.
        
        Args:
            config: Application configuration for validation rules
        """
        self._config = config
        self._max_file_size = config.processing.max_file_size_mb * 1024 * 1024

    def validate_pdf_file(self, file_path: Path) -> FileValidationResult:
        """Validate a PDF file for processing.
        
        Performs comprehensive validation including:
        - File existence and accessibility
        - Security checks (path traversal, permissions)
        - Size limits
        - File type verification
        - Basic PDF structure validation
        
        Args:
            file_path: Path to the PDF file to validate
            
        Returns:
            FileValidationResult with validation details
        """
        result = FileValidationResult(is_valid=True, file_path=file_path)

        try:
            # Security validation first (checks path patterns regardless of existence)
            self._validate_file_security(file_path, result)

            # Basic file existence and access checks
            self._validate_file_existence(file_path, result)
            if not result.is_valid:
                return result

            # File properties validation
            self._validate_file_properties(file_path, result)
            if not result.is_valid:
                return result

            # PDF-specific validation
            self._validate_pdf_structure(file_path, result)

        except Exception as e:
            result.add_error(f"Validation failed: {e}")

        return result

    def validate_output_path(self, output_path: Path, force: bool = False) -> FileValidationResult:
        """Validate output file path for writing.
        
        Args:
            output_path: Path where output will be written
            force: Whether to overwrite existing files
            
        Returns:
            FileValidationResult with validation details
        """
        result = FileValidationResult(is_valid=True, file_path=output_path)

        try:
            # Security check for output path first
            self._validate_output_security(output_path, result)
            if not result.is_valid:
                return result

            # Validate parent directory
            parent_dir = output_path.parent
            if not parent_dir.exists():
                result.add_error(f"Output directory does not exist: {parent_dir}")
                return result

            if not os.access(parent_dir, os.W_OK):
                result.add_error(f"No write permission for directory: {parent_dir}")
                return result

            # Check if output file already exists
            if output_path.exists():
                if not force:
                    result.add_error(
                        f"Output file already exists: {output_path}. "
                        "Use --force to overwrite."
                    )
                    return result
                else:
                    result.add_warning(f"Will overwrite existing file: {output_path}")

                # Check write permission on existing file
                if not os.access(output_path, os.W_OK):
                    result.add_error(f"No write permission for file: {output_path}")
                    return result

        except Exception as e:
            result.add_error(f"Output validation failed: {e}")

        return result

    def _validate_file_existence(self, file_path: Path, result: FileValidationResult) -> None:
        """Validate basic file existence and access.
        
        Args:
            file_path: Path to validate
            result: Result object to update
        """
        if not file_path.exists():
            result.add_error(f"File not found: {file_path}")
            return

        if not file_path.is_file():
            result.add_error(f"Not a regular file: {file_path}")
            return

        if not os.access(file_path, os.R_OK):
            result.add_error(f"File is not readable: {file_path}")
            return

    def _validate_file_security(self, file_path: Path, result: FileValidationResult) -> None:
        """Validate file path for security issues.
        
        Args:
            file_path: Path to validate
            result: Result object to update
        """
        try:
            # Resolve to absolute path to check for traversal attacks
            resolved_path = file_path.resolve()

            # Check for directory traversal attempts
            if '..' in str(file_path):
                result.add_warning("Path contains '..' components")

            # Ensure path is within reasonable bounds (not system directories)
            system_dirs = ['/etc', '/usr/bin', '/bin', '/sbin', '/boot', '/dev', '/proc', '/sys',
                          '/private/etc', '/private/usr/bin', '/private/bin', '/private/sbin']
            for sys_dir in system_dirs:
                if str(resolved_path).startswith(sys_dir):
                    result.add_error(f"Access to system directory not allowed: {sys_dir}")
                    return

        except (OSError, RuntimeError) as e:
            result.add_error(f"Path resolution failed: {e}")

    def _validate_file_properties(self, file_path: Path, result: FileValidationResult) -> None:
        """Validate file properties like size and type.
        
        Args:
            file_path: Path to validate
            result: Result object to update
        """
        try:
            # Get file statistics
            stat = file_path.stat()
            result.file_size = stat.st_size

            # Check file size
            if stat.st_size > self._max_file_size:
                max_mb = self._config.processing.max_file_size_mb
                actual_mb = stat.st_size / (1024 * 1024)
                result.add_error(
                    f"File size ({actual_mb:.1f}MB) exceeds limit ({max_mb}MB)"
                )
                return

            # Check for empty file
            if stat.st_size == 0:
                result.add_error("File is empty")
                return

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            result.mime_type = mime_type

            # Validate file extension
            if file_path.suffix.lower() != '.pdf':
                result.add_error(f"File must have .pdf extension, got: {file_path.suffix}")
                return

            # Warn if MIME type doesn't match
            if mime_type and mime_type != 'application/pdf':
                result.add_warning(f"Unexpected MIME type: {mime_type}")

        except OSError as e:
            result.add_error(f"Cannot read file properties: {e}")

    def _validate_pdf_structure(self, file_path: Path, result: FileValidationResult) -> None:
        """Perform basic PDF structure validation.
        
        Args:
            file_path: Path to validate
            result: Result object to update
        """
        try:
            # Read first few bytes to check PDF header
            with open(file_path, 'rb') as f:
                header = f.read(8)

            # Check PDF magic number
            if not header.startswith(b'%PDF-'):
                result.add_error("File does not appear to be a valid PDF (missing PDF header)")
                return

            # Extract PDF version
            try:
                version_part = header[5:8].decode('ascii')
                if not version_part[0].isdigit():
                    result.add_warning("Cannot determine PDF version")
                else:
                    # Add info about PDF version for debugging
                    result.add_warning(f"PDF version: {version_part}")
            except (UnicodeDecodeError, IndexError):
                result.add_warning("Cannot parse PDF version")

        except OSError as e:
            result.add_error(f"Cannot read PDF file: {e}")
        except Exception as e:
            result.add_warning(f"PDF validation warning: {e}")

    def _validate_output_security(self, output_path: Path, result: FileValidationResult) -> None:
        """Validate output path for security issues.
        
        Args:
            output_path: Output path to validate
            result: Result object to update
        """
        try:
            # Resolve to absolute path
            resolved_path = output_path.resolve()

            # Check for directory traversal in output path
            if '..' in str(output_path):
                result.add_warning("Output path contains '..' components")

            # Ensure we're not trying to write to system locations
            system_dirs = ['/etc', '/usr', '/bin', '/sbin', '/boot', '/dev', '/proc', '/sys',
                          '/private/etc', '/private/usr', '/private/bin', '/private/sbin']
            for sys_dir in system_dirs:
                if str(resolved_path).startswith(sys_dir):
                    result.add_error("Cannot write to system directory")
                    return

        except (OSError, RuntimeError) as e:
            result.add_error(f"Output path resolution failed: {e}")


def create_file_validator(config: ApplicationConfig) -> FileValidator:
    """Factory function to create configured file validator.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured FileValidator instance
    """
    return FileValidator(config)
