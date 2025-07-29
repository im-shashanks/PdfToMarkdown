"""
Interface for code detection following Clean Architecture principles.

This interface defines the contract for code block detection services.
"""

from abc import ABC
from abc import abstractmethod
from typing import List

from pdf2markdown.domain.models.document import CodeBlock
from pdf2markdown.domain.models.document import InlineCode
from pdf2markdown.domain.models.document import Line


class CodeDetectorInterface(ABC):
    """Interface for code detection services following Interface Segregation Principle."""

    @abstractmethod
    def is_monospace_font(self, font_family: str) -> bool:
        """
        Check if a font family is monospace.
        
        Args:
            font_family: Name of the font family to check
            
        Returns:
            True if the font is monospace, False otherwise
        """
        pass

    @abstractmethod
    def analyze_font_characteristics(self, lines: List[Line]) -> bool:
        """
        Analyze font characteristics to determine if text uses monospace fonts.
        
        Args:
            lines: List of lines to analyze
            
        Returns:
            True if lines appear to use consistent monospace characteristics
        """
        pass

    @abstractmethod
    def detect_code_blocks(self, lines: List[Line]) -> List[CodeBlock]:
        """
        Detect code blocks from a list of lines.
        
        Args:
            lines: List of lines to analyze for code blocks
            
        Returns:
            List of detected code blocks
        """
        pass

    @abstractmethod
    def detect_inline_code(self, line: Line) -> List[InlineCode]:
        """
        Detect inline code snippets within a single line.
        
        Args:
            line: Line to analyze for inline code
            
        Returns:
            List of detected inline code snippets
        """
        pass

    @abstractmethod
    def is_code_context(self, lines: List[Line], target_line_index: int) -> bool:
        """
        Determine if a line is in a code context (distinguishes from monospace headers).
        
        Args:
            lines: All lines for context analysis
            target_line_index: Index of the line to check
            
        Returns:
            True if the line appears to be in a code context
        """
        pass
