"""
Abstract interface for document formatting services.

This module defines the contract for document formatters,
enabling different output formats while maintaining clean architecture.
"""

from abc import ABC
from abc import abstractmethod

from pdf2markdown.domain.models import Document


class FormatterInterface(ABC):
    """Abstract interface for document formatting services.
    
    This interface defines the contract for converting documents
    to various output formats.
    """

    @abstractmethod
    def format_document(self, document: Document) -> str:
        """Format a document to string representation.
        
        Args:
            document: Document to format
            
        Returns:
            Formatted document as string
            
        Raises:
            ProcessingError: If formatting fails
        """
        pass

    @abstractmethod
    def format_to_file(self, document: Document, file_path: str) -> None:
        """Format a document and write to file.
        
        Args:
            document: Document to format
            file_path: Path where to write the formatted output
            
        Raises:
            ProcessingError: If formatting or file writing fails
        """
        pass
