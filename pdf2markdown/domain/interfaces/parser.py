"""Parser interfaces following Strategy pattern and Dependency Inversion Principle."""

from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Iterator
from typing import NamedTuple
from typing import Optional

from pdf2markdown.domain.models import Document


class TextElement(NamedTuple):
    """
    Represents a text element extracted from PDF with formatting information.
    
    This is a value object following Domain-Driven Design principles.
    """
    content: str
    font_size: float
    font_name: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False
    x_position: float = 0.0
    y_position: float = 0.0
    page_number: int = 1


class PdfParserStrategy(ABC):
    """
    Abstract interface for PDF parsing strategies.
    
    Follows:
    - Strategy Pattern: Allows different parsing implementations
    - Open/Closed Principle: Open for extension, closed for modification
    - Dependency Inversion: High-level modules depend on this abstraction
    """

    @abstractmethod
    def extract_text_elements(self, file_path: Path) -> Iterator[TextElement]:
        """
        Extract text elements from PDF with formatting information.
        
        Args:
            file_path: Path to the PDF file
            
        Yields:
            TextElement: Text elements with formatting metadata
            
        Raises:
            ValueError: If file cannot be parsed
            IOError: If file cannot be read
        """
        pass

    @abstractmethod
    def parse_document(self, file_path: Path) -> Document:
        """
        Parse PDF file into a Document model.
        
        This is a higher-level method that uses extract_text_elements
        and applies heading detection logic.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Document: Parsed document with detected structure
            
        Raises:
            ValueError: If file cannot be parsed
            IOError: If file cannot be read
        """
        pass
