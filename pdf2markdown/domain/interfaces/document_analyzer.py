"""Document analyzer interface for document type recognition."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from pdf2markdown.domain.models import Document


class DocumentType(Enum):
    """Enumeration of supported document types."""
    RESUME = "resume"
    ACADEMIC_PAPER = "academic_paper"
    BUSINESS_DOCUMENT = "business_document"
    MANUAL = "manual"
    REPORT = "report"
    UNKNOWN = "unknown"


@dataclass
class DocumentAnalysis:
    """
    Analysis result containing document type and confidence metrics.
    
    Follows Value Object pattern - immutable analysis result.
    """
    document_type: DocumentType
    confidence: float  # 0.0 to 1.0
    characteristics: Dict[str, float]  # Feature scores
    suggested_processing_strategy: str

    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if analysis confidence meets threshold."""
        return self.confidence >= threshold


class DocumentAnalyzerInterface(ABC):
    """
    Interface for document type analysis and recognition.
    
    Follows Interface Segregation Principle - focused on document analysis only.
    """

    @abstractmethod
    def analyze_document_type(self, document: Document) -> DocumentAnalysis:
        """
        Analyze document to determine its type and characteristics.
        
        Args:
            document: Document to analyze
            
        Returns:
            DocumentAnalysis: Analysis result with type and confidence
        """
        pass

    @abstractmethod
    def get_processing_recommendations(self, analysis: DocumentAnalysis) -> Dict[str, any]:
        """
        Get processing recommendations based on document analysis.
        
        Args:
            analysis: Document analysis result
            
        Returns:
            Dict: Processing recommendations (heading thresholds, paragraph settings, etc.)
        """
        pass
