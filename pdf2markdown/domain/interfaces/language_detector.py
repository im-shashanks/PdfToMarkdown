"""
Interface for programming language detection following Clean Architecture principles.

This interface defines the contract for language detection services.
"""

from abc import ABC
from abc import abstractmethod

from pdf2markdown.domain.models.document import CodeBlock
from pdf2markdown.domain.models.document import CodeLanguage


class LanguageDetectorInterface(ABC):
    """Interface for programming language detection services following Interface Segregation Principle."""

    @abstractmethod
    def detect_language(self, code_content: str) -> CodeLanguage:
        """
        Detect the programming language of code content.
        
        Args:
            code_content: The code content to analyze
            
        Returns:
            Detected programming language or UNKNOWN if cannot be determined
        """
        pass

    @abstractmethod
    def detect_language_from_keywords(self, code_content: str) -> CodeLanguage:
        """
        Detect language based on keyword patterns.
        
        Args:
            code_content: The code content to analyze
            
        Returns:
            Detected programming language based on keywords
        """
        pass

    @abstractmethod
    def detect_language_from_syntax(self, code_content: str) -> CodeLanguage:
        """
        Detect language based on syntax patterns.
        
        Args:
            code_content: The code content to analyze
            
        Returns:
            Detected programming language based on syntax patterns
        """
        pass

    @abstractmethod
    def analyze_code_block(self, code_block: CodeBlock) -> CodeBlock:
        """
        Analyze a code block and update it with detected language.
        
        Args:
            code_block: The code block to analyze
            
        Returns:
            Code block with updated language information
        """
        pass

    @abstractmethod
    def get_confidence_score(self, code_content: str, language: CodeLanguage) -> float:
        """
        Get confidence score for a specific language detection.
        
        Args:
            code_content: The code content to analyze
            language: The language to score confidence for
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass
