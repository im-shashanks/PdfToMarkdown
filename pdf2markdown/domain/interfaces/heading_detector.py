"""
Abstract interface for heading detection services.

This module defines the contract for heading detection implementations,
following the Interface Segregation Principle and enabling dependency injection.
"""

from abc import ABC, abstractmethod

from pdf2markdown.domain.models import Document


class HeadingDetectorInterface(ABC):
    """Abstract interface for heading detection services.
    
    This interface defines the contract for detecting headings in documents,
    allowing for different detection strategies and algorithms.
    """

    @abstractmethod
    def detect_headings_in_document(self, document: Document) -> Document:
        """Detect headings in a document and return an updated document.
        
        Args:
            document: Document to analyze for headings
            
        Returns:
            Document with detected headings converted from text blocks
            
        Raises:
            ProcessingError: If heading detection fails
        """
        pass