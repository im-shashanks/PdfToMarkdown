"""Document type analyzer implementing intelligent document recognition."""

import logging
import re
from typing import Dict
from typing import Optional

from pdf2markdown.domain.interfaces.document_analyzer import DocumentAnalysis
from pdf2markdown.domain.interfaces.document_analyzer import DocumentAnalyzerInterface
from pdf2markdown.domain.interfaces.document_analyzer import DocumentType
from pdf2markdown.domain.models import Document


class DocumentAnalyzer(DocumentAnalyzerInterface):
    """
    Service for analyzing and classifying document types.
    
    Follows Single Responsibility Principle - focused on document type analysis.
    Uses Strategy pattern for different analysis algorithms.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize document analyzer."""
        self.logger = logger or logging.getLogger(__name__)

        # Resume-specific patterns
        self.resume_keywords = {
            'experience', 'education', 'skills', 'summary', 'objective',
            'qualifications', 'achievements', 'certifications', 'awards',
            'projects', 'career', 'professional', 'employment', 'work',
            'background', 'expertise', 'accomplishments', 'technical'
        }

        # Academic paper patterns
        self.academic_keywords = {
            'abstract', 'introduction', 'methodology', 'results', 'conclusion',
            'references', 'bibliography', 'literature', 'research', 'study',
            'analysis', 'findings', 'discussion', 'hypothesis', 'experimental'
        }

        # Business document patterns
        self.business_keywords = {
            'executive', 'summary', 'overview', 'proposal', 'budget',
            'revenue', 'profit', 'quarterly', 'annual', 'strategic',
            'objectives', 'goals', 'metrics', 'performance', 'roi'
        }

        # Manual/technical document patterns
        self.manual_keywords = {
            'installation', 'configuration', 'setup', 'troubleshooting',
            'chapter', 'section', 'procedure', 'steps', 'instructions',
            'requirements', 'specifications', 'guidelines', 'manual'
        }

    def analyze_document_type(self, document: Document) -> DocumentAnalysis:
        """
        Analyze document to determine its type using multi-criteria analysis.
        
        Args:
            document: Document to analyze
            
        Returns:
            DocumentAnalysis: Comprehensive analysis result
        """
        if not document.blocks:
            return DocumentAnalysis(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                characteristics={},
                suggested_processing_strategy="default"
            )

        # Extract text content for analysis
        text_content = self._extract_text_content(document)

        # Multi-criteria analysis
        characteristics = {}

        # 1. Keyword-based analysis
        keyword_scores = self._analyze_keywords(text_content)
        characteristics.update(keyword_scores)

        # 2. Structure analysis
        structure_scores = self._analyze_document_structure(document)
        characteristics.update(structure_scores)

        # 3. Formatting pattern analysis
        format_scores = self._analyze_formatting_patterns(document)
        characteristics.update(format_scores)

        # 4. Length and density analysis
        length_scores = self._analyze_document_metrics(document)
        characteristics.update(length_scores)

        # Determine document type and confidence
        document_type, confidence = self._classify_document_type(characteristics)

        # Get processing strategy
        strategy = self._get_processing_strategy(document_type, characteristics)

        return DocumentAnalysis(
            document_type=document_type,
            confidence=confidence,
            characteristics=characteristics,
            suggested_processing_strategy=strategy
        )

    def get_processing_recommendations(self, analysis: DocumentAnalysis) -> Dict[str, any]:
        """
        Get processing recommendations based on document analysis.
        
        Args:
            analysis: Document analysis result
            
        Returns:
            Dict: Processing recommendations
        """
        recommendations = {}

        if analysis.document_type == DocumentType.RESUME:
            recommendations.update({
                'heading_detection': {
                    'font_size_threshold': 0.05,  # More sensitive for resumes
                    'pattern_weight': 2.0,  # Heavy emphasis on section patterns
                    'caps_weight': 1.5,  # ALL CAPS sections common in resumes
                    'enable_semantic_detection': True
                },
                'paragraph_detection': {
                    'merge_aggressive': False,  # Keep resume sections distinct
                    'line_spacing_threshold': 1.3,  # Tighter spacing detection
                    'preserve_lists': True  # Preserve bullet points
                },
                'formatting': {
                    'preserve_indentation': True,
                    'detect_lists': True,
                    'section_spacing': 'double'
                }
            })
        elif analysis.document_type == DocumentType.ACADEMIC_PAPER:
            recommendations.update({
                'heading_detection': {
                    'font_size_threshold': 0.2,  # Less sensitive, academic papers use subtle headings
                    'pattern_weight': 1.0,
                    'caps_weight': 0.5,  # Less emphasis on ALL CAPS
                    'enable_semantic_detection': True
                },
                'paragraph_detection': {
                    'merge_aggressive': True,  # Merge academic paragraphs
                    'line_spacing_threshold': 1.8,  # Looser spacing detection
                    'preserve_lists': False
                },
                'formatting': {
                    'preserve_indentation': False,
                    'detect_lists': False,
                    'section_spacing': 'single'
                }
            })
        else:  # Default/unknown documents
            recommendations.update({
                'heading_detection': {
                    'font_size_threshold': 0.1,
                    'pattern_weight': 1.0,
                    'caps_weight': 1.0,
                    'enable_semantic_detection': True
                },
                'paragraph_detection': {
                    'merge_aggressive': False,
                    'line_spacing_threshold': 1.5,
                    'preserve_lists': True
                },
                'formatting': {
                    'preserve_indentation': True,
                    'detect_lists': True,
                    'section_spacing': 'single'
                }
            })

        return recommendations

    def _extract_text_content(self, document: Document) -> str:
        """Extract all text content from document for analysis."""
        text_parts = []
        for block in document.blocks:
            if hasattr(block, 'content') and block.content:
                text_parts.append(block.content.strip())
        return ' '.join(text_parts).lower()

    def _analyze_keywords(self, text_content: str) -> Dict[str, float]:
        """Analyze keyword patterns to identify document type indicators."""
        words = set(re.findall(r'\b\w+\b', text_content.lower()))

        resume_score = len(words.intersection(self.resume_keywords)) / len(self.resume_keywords)
        academic_score = len(words.intersection(self.academic_keywords)) / len(self.academic_keywords)
        business_score = len(words.intersection(self.business_keywords)) / len(self.business_keywords)
        manual_score = len(words.intersection(self.manual_keywords)) / len(self.manual_keywords)

        return {
            'resume_keyword_score': resume_score,
            'academic_keyword_score': academic_score,
            'business_keyword_score': business_score,
            'manual_keyword_score': manual_score
        }

    def _analyze_document_structure(self, document: Document) -> Dict[str, float]:
        """Analyze document structure patterns."""
        total_blocks = len(document.blocks)
        if total_blocks == 0:
            return {'structure_score': 0.0}

        # Analyze block types and patterns
        short_blocks = sum(1 for block in document.blocks
                          if hasattr(block, 'content') and len(block.content.strip()) < 50)
        medium_blocks = sum(1 for block in document.blocks
                           if hasattr(block, 'content') and 50 <= len(block.content.strip()) < 200)
        long_blocks = sum(1 for block in document.blocks
                         if hasattr(block, 'content') and len(block.content.strip()) >= 200)

        short_ratio = short_blocks / total_blocks
        medium_ratio = medium_blocks / total_blocks
        long_ratio = long_blocks / total_blocks

        # Resume characteristic: Many short blocks (section headers, bullet points)
        resume_structure_score = short_ratio * 0.6 + medium_ratio * 0.4

        # Academic characteristic: Fewer, longer blocks (paragraphs)
        academic_structure_score = long_ratio * 0.7 + medium_ratio * 0.3

        return {
            'short_block_ratio': short_ratio,
            'medium_block_ratio': medium_ratio,
            'long_block_ratio': long_ratio,
            'resume_structure_score': resume_structure_score,
            'academic_structure_score': academic_structure_score
        }

    def _analyze_formatting_patterns(self, document: Document) -> Dict[str, float]:
        """Analyze formatting and style patterns."""
        total_blocks = len(document.blocks)
        if total_blocks == 0:
            return {'formatting_score': 0.0}

        # Count formatting characteristics
        caps_blocks = 0
        bold_blocks = 0
        varied_font_blocks = 0

        for block in document.blocks:
            if hasattr(block, 'content') and block.content:
                content = block.content.strip()
                if content.isupper() and len(content) > 2:
                    caps_blocks += 1
                if hasattr(block, 'is_bold') and getattr(block, 'is_bold', False):
                    bold_blocks += 1

        caps_ratio = caps_blocks / total_blocks
        bold_ratio = bold_blocks / total_blocks

        # Resume characteristic: More ALL CAPS headings and bold text
        resume_format_score = caps_ratio * 0.7 + bold_ratio * 0.3

        return {
            'caps_ratio': caps_ratio,
            'bold_ratio': bold_ratio,
            'resume_format_score': resume_format_score
        }

    def _analyze_document_metrics(self, document: Document) -> Dict[str, float]:
        """Analyze document length and density metrics."""
        total_chars = sum(len(block.content) for block in document.blocks
                         if hasattr(block, 'content') and block.content)
        total_words = len(re.findall(r'\b\w+\b',
                                   ' '.join(block.content for block in document.blocks
                                           if hasattr(block, 'content') and block.content)))

        # Document length characteristics
        is_short = total_words < 1000  # Typical resume length
        is_medium = 1000 <= total_words < 5000
        is_long = total_words >= 5000  # Typical academic paper length

        return {
            'total_words': total_words,
            'total_chars': total_chars,
            'is_short_document': float(is_short),
            'is_medium_document': float(is_medium),
            'is_long_document': float(is_long)
        }

    def _classify_document_type(self, characteristics: Dict[str, float]) -> tuple[DocumentType, float]:
        """Classify document type based on characteristic scores."""

        # Calculate composite scores for each document type
        resume_score = (
            characteristics.get('resume_keyword_score', 0) * 0.3 +
            characteristics.get('resume_structure_score', 0) * 0.25 +
            characteristics.get('resume_format_score', 0) * 0.25 +
            characteristics.get('is_short_document', 0) * 0.2
        )

        academic_score = (
            characteristics.get('academic_keyword_score', 0) * 0.4 +
            characteristics.get('academic_structure_score', 0) * 0.3 +
            characteristics.get('is_long_document', 0) * 0.3
        )

        business_score = (
            characteristics.get('business_keyword_score', 0) * 0.5 +
            characteristics.get('is_medium_document', 0) * 0.3 +
            characteristics.get('caps_ratio', 0) * 0.2
        )

        manual_score = (
            characteristics.get('manual_keyword_score', 0) * 0.6 +
            characteristics.get('is_long_document', 0) * 0.4
        )

        # Determine best match
        scores = {
            DocumentType.RESUME: resume_score,
            DocumentType.ACADEMIC_PAPER: academic_score,
            DocumentType.BUSINESS_DOCUMENT: business_score,
            DocumentType.MANUAL: manual_score
        }

        best_type = max(scores.items(), key=lambda x: x[1])

        # Require minimum confidence threshold
        if best_type[1] < 0.3:
            return DocumentType.UNKNOWN, best_type[1]

        return best_type[0], best_type[1]

    def _get_processing_strategy(self, doc_type: DocumentType, characteristics: Dict[str, float]) -> str:
        """Determine processing strategy based on document type."""
        if doc_type == DocumentType.RESUME:
            return "resume_optimized"
        elif doc_type == DocumentType.ACADEMIC_PAPER:
            return "academic_optimized"
        elif doc_type == DocumentType.BUSINESS_DOCUMENT:
            return "business_optimized"
        elif doc_type == DocumentType.MANUAL:
            return "manual_optimized"
        else:
            return "adaptive_balanced"
