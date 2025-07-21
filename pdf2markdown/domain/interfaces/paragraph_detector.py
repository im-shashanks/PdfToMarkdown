"""Interface for paragraph detection following Dependency Inversion Principle."""

from abc import ABC
from abc import abstractmethod
from typing import List

from pdf2markdown.domain.models.document import Document
from pdf2markdown.domain.models.document import Paragraph
from pdf2markdown.domain.models.document import TextBlock


class ParagraphDetectorInterface(ABC):
    """
    Interface for paragraph detection services.
    
    Follows Interface Segregation Principle - focused on paragraph detection only.
    """

    @abstractmethod
    def detect_paragraphs_in_document(self, document: Document) -> Document:
        """
        Detect paragraphs in a document and replace TextBlocks with Paragraphs.
        
        Args:
            document: Document containing TextBlocks to analyze
            
        Returns:
            Document with TextBlocks converted to Paragraphs where appropriate
        """
        pass

    @abstractmethod
    def convert_text_block_to_paragraph(self, text_block: TextBlock) -> Paragraph:
        """
        Convert a single TextBlock to a Paragraph.
        
        Args:
            text_block: TextBlock to convert
            
        Returns:
            Paragraph with detected text flow and formatting
        """
        pass

    @abstractmethod
    def merge_continuous_paragraphs(self, paragraphs: List[Paragraph]) -> List[Paragraph]:
        """
        Merge paragraphs that should be continuous based on text flow analysis.
        
        Args:
            paragraphs: List of paragraphs to analyze for merging
            
        Returns:
            List of paragraphs with continuous ones merged
        """
        pass

    @abstractmethod
    def detect_paragraphs_from_pdf(self, file_path) -> Document:
        """
        Detect paragraphs directly from PDF file using line-level coordinate analysis.
        
        This method provides more accurate paragraph detection by working
        directly with PDF coordinate data rather than pre-processed text blocks.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Document with paragraphs detected using actual PDF coordinates
        """
        pass
