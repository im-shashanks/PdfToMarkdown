"""
Core exception classes for PdfToMarkdown application.

This module defines the exception hierarchy used throughout the application,
following enterprise security and error handling best practices.
"""

from typing import Optional


class PdfToMarkdownError(Exception):
    """Base exception class for all PdfToMarkdown errors.
    
    This base class provides a common interface for all application-specific
    exceptions and includes structured error information for better debugging
    and user feedback.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None
    ) -> None:
        """Initialize the exception with structured error information.
        
        Args:
            message: Human-readable error description
            error_code: Optional error code for programmatic handling
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.message


class ValidationError(PdfToMarkdownError):
    """Raised when input validation fails.
    
    This exception is used for all input validation failures,
    including invalid file paths, unsupported file types, and
    malformed configuration.
    """

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        """Initialize validation error with field information.
        
        Args:
            message: Validation error description
            field: Optional field name that failed validation
        """
        details = {"field": field} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details)


class InvalidPdfError(PdfToMarkdownError):
    """Raised when PDF file is invalid or corrupted.
    
    This exception is used when a file appears to be a PDF but
    cannot be processed due to corruption, encryption, or
    unsupported PDF features.
    """

    def __init__(self, message: str, file_path: Optional[str] = None) -> None:
        """Initialize PDF error with file path information.
        
        Args:
            message: Error description
            file_path: Optional path to the problematic PDF file
        """
        details = {"file_path": file_path} if file_path else {}
        super().__init__(message, "INVALID_PDF", details)


class ProcessingError(PdfToMarkdownError):
    """Raised when PDF processing fails during conversion.
    
    This exception is used for errors that occur during the PDF
    parsing and markdown conversion process.
    """

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> None:
        """Initialize processing error with stage and file information.
        
        Args:
            message: Error description
            stage: Optional processing stage where error occurred
            file_path: Optional path to the file being processed
        """
        details = {}
        if stage:
            details["stage"] = stage
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, "PROCESSING_ERROR", details)


class FileSystemError(PdfToMarkdownError):
    """Raised when file system operations fail.
    
    This exception is used for file I/O errors, permission issues,
    and other file system related problems.
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> None:
        """Initialize file system error with operation details.
        
        Args:
            message: Error description
            operation: Optional operation that failed (read, write, etc.)
            file_path: Optional path to the problematic file
        """
        details = {}
        if operation:
            details["operation"] = operation
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, "FILESYSTEM_ERROR", details)


class ConfigurationError(PdfToMarkdownError):
    """Raised when application configuration is invalid.
    
    This exception is used for configuration-related errors,
    including invalid settings, missing required configuration,
    and environment setup issues.
    """

    def __init__(self, message: str, config_key: Optional[str] = None) -> None:
        """Initialize configuration error with key information.
        
        Args:
            message: Error description
            config_key: Optional configuration key that caused the error
        """
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, "CONFIGURATION_ERROR", details)
