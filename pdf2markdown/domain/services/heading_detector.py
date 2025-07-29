"""Heading detection service following Domain-Driven Design principles."""

import logging
import statistics
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional

from pdf2markdown.domain.interfaces import HeadingDetectorInterface
from pdf2markdown.domain.interfaces import TextElement
from pdf2markdown.domain.models import Block
from pdf2markdown.domain.models import Document
from pdf2markdown.domain.models import Heading
from pdf2markdown.domain.models import TextBlock


@dataclass
class HeadingDetectionConfig:
    """
    Configuration for heading detection algorithm.
    
    Follows Single Responsibility Principle - only responsible for config data.
    """
    # Font size multipliers for each heading level (H1-H6) - Adjusted for better detection
    level_multipliers: Dict[int, float] = field(default_factory=lambda: {
        1: 1.8,    # H1: 1.8x base size (more realistic for resumes)
        2: 1.5,    # H2: 1.5x base size
        3: 1.3,    # H3: 1.3x base size
        4: 1.15,   # H4: 1.15x base size
        5: 1.05,   # H5: 1.05x base size
        6: 1.02,   # H6: 1.02x base size (captures subtle headings)
    })

    # Minimum font size difference to consider text a heading (more permissive)
    min_size_difference: float = 0.1

    # Weight factor for bold text in heading detection
    bold_weight: float = 0.1

    # Weight factor for italic text in heading detection
    italic_weight: float = 0.05

    # Minimum content length to be considered a heading
    min_heading_length: int = 1

    # Maximum content length to be considered a heading
    max_heading_length: int = 200


class HeadingDetector(HeadingDetectorInterface):
    """
    Service for detecting headings in document text elements.
    
    Follows:
    - Single Responsibility: Only responsible for heading detection
    - Dependency Inversion: Depends on abstractions (TextElement, Block)
    - Open/Closed: Open for extension via configuration
    """

    def __init__(self, config: Optional[HeadingDetectionConfig] = None) -> None:
        """Initialize heading detector with configuration."""
        self.config = config or HeadingDetectionConfig()
        self.logger = logging.getLogger(__name__)

    def detect_headings_in_document(self, document: Document) -> Document:
        """
        Analyze document blocks and convert appropriate text blocks to headings.
        
        This is the main entry point for heading detection.
        
        Args:
            document: Document with text blocks to analyze
            
        Returns:
            Document: New document with headings detected and converted
        """
        if not document.blocks:
            self.logger.warning("Document has no blocks to analyze")
            return document

        # Extract text elements from document blocks
        text_elements = self._extract_text_elements_from_blocks(document.blocks)

        if not text_elements:
            self.logger.warning("No text elements found in document")
            return document

        # Analyze font sizes to establish baseline
        baseline_font_size = self._calculate_baseline_font_size(text_elements)
        self.logger.info(f"Calculated baseline font size: {baseline_font_size:.1f}pt")

        # Create new document with detected headings
        new_document = Document(
            title=document.title,
            metadata=document.metadata.copy()
        )

        # Process each block and determine if it should be a heading
        for block in document.blocks:
            # Handle both TextBlock and Paragraph objects
            if ((isinstance(block, TextBlock) or hasattr(block, 'lines'))
                and hasattr(block, 'font_size') and block.font_size):
                heading_level = self._determine_heading_level(
                    block, baseline_font_size
                )

                if heading_level:
                    # Convert to heading
                    heading = Heading(
                        level=heading_level,
                        content=block.content,
                        font_size=block.font_size,
                        is_bold=self._is_likely_bold(block)
                    )
                    new_document.add_block(heading)
                    self.logger.debug(f"Detected H{heading_level}: {block.content[:50]}...")
                else:
                    # Keep as text block or paragraph
                    new_document.add_block(block)
            else:
                # Keep non-text blocks as-is
                new_document.add_block(block)

        return new_document

    def _extract_text_elements_from_blocks(self, blocks: List[Block]) -> List[TextElement]:
        """Extract text elements from document blocks for analysis."""
        text_elements = []

        for block in blocks:
            if isinstance(block, TextBlock) and block.font_size:
                # Create a TextElement from the TextBlock for analysis
                element = TextElement(
                    content=block.content,
                    font_size=block.font_size,
                    is_bold=getattr(block, 'is_bold', False)
                )
                text_elements.append(element)
            elif hasattr(block, 'lines') and hasattr(block, 'font_size') and block.font_size:
                # Handle Paragraph objects (after paragraph detection)
                element = TextElement(
                    content=block.content,
                    font_size=block.font_size,
                    is_bold=getattr(block, 'is_bold', False)
                )
                text_elements.append(element)

        return text_elements

    def _calculate_baseline_font_size(self, text_elements: List[TextElement]) -> float:
        """
        Calculate the baseline (most common) font size using robust statistical analysis.
        
        Uses frequency analysis, mode detection, and filtering to find the most
        representative body text font size.
        """
        if not text_elements:
            return 12.0  # Default font size

        font_sizes = [element.font_size for element in text_elements]

        # Remove extreme outliers (very large or small fonts)
        sorted_sizes = sorted(font_sizes)
        q1_idx = len(sorted_sizes) // 4
        q3_idx = 3 * len(sorted_sizes) // 4

        if len(sorted_sizes) > 4:
            # Use interquartile range to filter outliers
            q1 = sorted_sizes[q1_idx]
            q3 = sorted_sizes[q3_idx]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            filtered_sizes = [size for size in font_sizes
                            if lower_bound <= size <= upper_bound]
        else:
            filtered_sizes = font_sizes

        if not filtered_sizes:
            filtered_sizes = font_sizes

        # Try multiple approaches to find baseline
        try:
            # Primary: Most frequent font size (mode)
            return statistics.mode(filtered_sizes)
        except statistics.StatisticsError:
            # Fallback 1: Median of filtered sizes (robust central tendency)
            if len(filtered_sizes) > 1:
                return statistics.median(filtered_sizes)
            # Fallback 2: Use most common size from frequency analysis
            size_counts = {}
            for size in font_sizes:
                size_counts[size] = size_counts.get(size, 0) + 1

            if size_counts:
                most_common_size = max(size_counts.items(), key=lambda x: x[1])[0]
                return most_common_size

            # Final fallback
            return min(font_sizes) if font_sizes else 12.0

    def _determine_heading_level(
        self,
        block: Block,
        baseline_font_size: float
    ) -> Optional[int]:
        """
        Resume-aware heading detection prioritizing content patterns over font size.
        
        Strategy: Content-first analysis with semantic understanding of resume structure.
        
        Args:
            block: TextBlock or Paragraph object to analyze
            baseline_font_size: Baseline font size for comparison
        
        Returns:
            int: Heading level (1-6) or None if not a heading
        """
        if not hasattr(block, 'font_size') or not block.font_size:
            return None

        content = block.content.strip()

        # Check content length constraints (more permissive for section headers)
        content_length = len(content)
        if content_length < 1 or content_length > 300:  # Increased limit for resume sections
            return None

        # Exclude content that looks like contact information
        if self._is_contact_information(content):
            return None

        # CONTENT-FIRST ANALYSIS: Check for explicit resume section headers
        resume_section_level = self._detect_resume_section_header(content)
        if resume_section_level:
            return resume_section_level

        # Check for name/title patterns (H1 candidates)
        if self._is_likely_name_or_title(content):
            return 1

        # Font size analysis (secondary criterion)
        size_ratio = block.font_size / baseline_font_size

        # Style characteristics
        style_bonus = 0.0
        if self._is_likely_bold(block):
            style_bonus += 0.5

        # ALL CAPS analysis (strong indicator for resume sections)
        if content.isupper() and len(content.split()) <= 4:
            style_bonus += 1.0

        # Calculate total heading score
        heading_score = style_bonus

        # Add font size contribution (reduced weight)
        if size_ratio > 1.05:  # At least 5% larger than baseline
            heading_score += min((size_ratio - 1.0) * 2.0, 1.0)  # Cap font size contribution

        # Determine level based on combined analysis
        if heading_score >= 1.5:
            # Use semantic context to determine level
            if self._is_major_section_keyword(content):
                return 2  # Major sections (EXPERIENCE, EDUCATION, etc.)
            elif size_ratio >= 1.3:
                return 3  # Subsections with larger font
            elif style_bonus >= 1.0:  # ALL CAPS or bold
                return 4  # Styled subsections
            else:
                return 5  # Minor headings

        elif heading_score >= 0.8 and size_ratio > 1.1:
            return 6  # Weak headings

        return None

    def _is_likely_bold(self, block: Block) -> bool:
        """Determine if block is likely bold formatted."""
        # This is a simple heuristic - in a real implementation,
        # we would get this information from the PDF parser
        return getattr(block, 'is_bold', False)

    def _detect_resume_section_header(self, content: str) -> Optional[int]:
        """
        Detect explicit resume section headers with high confidence.
        
        Returns:
            int: Heading level for resume sections, or None if not a section header
        """
        content_clean = content.strip().upper()

        # Primary resume sections (H2 level)
        primary_sections = {
            'PROFESSIONAL SUMMARY', 'EXECUTIVE SUMMARY', 'SUMMARY', 'OBJECTIVE',
            'CAREER OBJECTIVE', 'PROFESSIONAL OBJECTIVE',
            'EXPERIENCE', 'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE',
            'CAREER EXPERIENCE', 'EMPLOYMENT HISTORY', 'WORK HISTORY',
            'EDUCATION', 'EDUCATIONAL BACKGROUND', 'ACADEMIC BACKGROUND',
            'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'KEY SKILLS',
            'CERTIFICATIONS', 'CERTIFICATES', 'PROFESSIONAL CERTIFICATIONS',
            'AWARDS', 'HONORS', 'ACHIEVEMENTS', 'ACCOMPLISHMENTS',
            'PROJECTS', 'KEY PROJECTS', 'NOTABLE PROJECTS',
            'PUBLICATIONS', 'RESEARCH', 'PUBLICATIONS AND RESEARCH',
            'REFERENCES', 'PROFESSIONAL REFERENCES'
        }

        # Check for exact matches
        if content_clean in primary_sections:
            return 2

        # Check for partial matches (single word sections)
        single_word_sections = {
            'SUMMARY', 'OBJECTIVE', 'EXPERIENCE', 'EDUCATION', 'SKILLS',
            'CERTIFICATIONS', 'AWARDS', 'PROJECTS', 'PUBLICATIONS', 'REFERENCES'
        }

        if content_clean in single_word_sections:
            return 2

        # Check for section headers with additional text
        for section in primary_sections:
            if section in content_clean and len(content_clean) <= len(section) + 20:
                return 2

        return None

    def _is_likely_name_or_title(self, content: str) -> bool:
        """
        Detect if content appears to be a person's name or professional title.
        
        Returns:
            bool: True if content appears to be a name/title (H1 candidate)
        """
        content = content.strip()
        words = content.split()

        # Simple heuristics for names
        if (2 <= len(words) <= 4 and  # Reasonable name length
            len(content) <= 50 and  # Not too long
            all(word[0].isupper() for word in words if word) and  # Title case
            not any(char.isdigit() for char in content) and  # No numbers
            not content.endswith(('.', '!', '?', ':', ';'))):  # No terminal punctuation

            # Additional checks to avoid false positives
            name_indicators = ['jr', 'sr', 'iii', 'phd', 'md', 'pe', 'cpa']
            business_words = ['company', 'corporation', 'manager', 'director', 'engineer']

            content_lower = content.lower()

            # Likely a name if it has name suffixes
            if any(indicator in content_lower for indicator in name_indicators):
                return True

            # Less likely if it contains business terms
            if any(word in content_lower for word in business_words):
                return False

            # If it's just 2-3 capitalized words, likely a name
            if 2 <= len(words) <= 3:
                return True

        return False

    def _is_major_section_keyword(self, content: str) -> bool:
        """
        Check if content contains major resume section keywords.
        
        Returns:
            bool: True if content contains major section keywords
        """
        content_lower = content.lower()
        major_keywords = {
            'experience', 'education', 'skills', 'summary', 'objective',
            'certifications', 'awards', 'projects', 'publications'
        }

        return any(keyword in content_lower for keyword in major_keywords)

    def _analyze_heading_context(self, content: str) -> float:
        """
        Analyze contextual indicators for heading detection.
        
        Returns:
            float: Context score (0.0 to 1.0) for heading likelihood
        """
        context_score = 0.0

        # Short, standalone lines are more likely to be headings
        word_count = len(content.split())
        if word_count <= 5:
            context_score += 0.3
        elif word_count <= 10:
            context_score += 0.1

        # Lines without terminal punctuation
        if not content.endswith(('.', '!', '?', ':', ';')):
            context_score += 0.2

        # Lines with specific formatting
        if content.isupper():
            context_score += 0.3
        elif content.istitle():  # Title Case
            context_score += 0.2

        return min(context_score, 1.0)  # Cap at 1.0

    def _is_all_caps_section_heading(self, content: str) -> bool:
        """Enhanced ALL CAPS section heading detection."""
        content = content.strip()

        # Must be ALL CAPS
        if not content.isupper():
            return False

        # Must contain mostly letters (not just symbols/numbers)
        letter_count = sum(1 for c in content if c.isalpha())
        if letter_count < len(content) * 0.6:  # At least 60% letters (relaxed)
            return False

        # Reasonable length for section headings
        if len(content) < 2 or len(content) > 80:  # More permissive range
            return False

        # Enhanced section heading patterns (more comprehensive)
        section_keywords = {
            'EDUCATION', 'SKILLS', 'EXPERIENCE', 'WORK', 'PROJECTS',
            'CERTIFICATIONS', 'AWARDS', 'SUMMARY', 'OBJECTIVE',
            'BACKGROUND', 'QUALIFICATIONS', 'ACHIEVEMENTS', 'CAREER',
            'PROFESSIONAL', 'TECHNICAL', 'EMPLOYMENT', 'ACADEMIC',
            'RESEARCH', 'VOLUNTEER', 'ACTIVITIES', 'INTERESTS',
            'LANGUAGES', 'SOFTWARE', 'TOOLS', 'METHODOLOGIES',
            'PUBLICATIONS', 'REFERENCES', 'HONORS', 'ACCOMPLISHMENTS',
            'COMPETENCIES', 'EXPERTISE', 'HISTORY'
        }

        # Check if content contains any section keywords
        content_words = set(content.split())
        if content_words.intersection(section_keywords):
            return True

        # Check if it's a short ALL CAPS phrase (likely a heading)
        if len(content.split()) <= 4 and len(content) <= 30:
            return True

        return False

    def _is_contact_information(self, content: str) -> bool:
        """Determine if content appears to be contact information."""
        content = content.lower().strip()

        # Contact info patterns
        contact_indicators = [
            '@',  # Email addresses
            'www.',  # Websites
            'http',  # URLs
            '(',  # Phone numbers with parentheses
            '-',  # Phone numbers with dashes
            'linkedin',  # Social media
            'github',  # Code repositories
            'portfolio',  # Portfolio links
        ]

        # If content contains multiple contact indicators, likely contact info
        indicator_count = sum(1 for indicator in contact_indicators if indicator in content)

        # Contact info typically has multiple indicators (email + phone + links)
        return indicator_count >= 2
