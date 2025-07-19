"""Heading detection service following Domain-Driven Design principles."""

import logging
import statistics
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional

from pdf2markdown.domain.interfaces import HeadingDetectorInterface, TextElement
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
    # Font size multipliers for each heading level (H1-H6)
    level_multipliers: Dict[int, float] = field(default_factory=lambda: {
        1: 2.0,    # H1: 2x base size
        2: 1.8,    # H2: 1.8x base size
        3: 1.5,    # H3: 1.5x base size
        4: 1.3,    # H4: 1.3x base size
        5: 1.2,    # H5: 1.2x base size
        6: 1.1,    # H6: 1.1x base size
    })

    # Minimum font size difference to consider text a heading
    min_size_difference: float = 1.0

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
            if isinstance(block, TextBlock) and block.font_size:
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
                    # Keep as text block
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

        return text_elements

    def _calculate_baseline_font_size(self, text_elements: List[TextElement]) -> float:
        """
        Calculate the baseline (most common) font size in the document.
        
        Uses statistical mode or median as fallback.
        """
        if not text_elements:
            return 12.0  # Default font size

        font_sizes = [element.font_size for element in text_elements]

        try:
            # Try to find the most common font size (mode)
            return statistics.mode(font_sizes)
        except statistics.StatisticsError:
            # If no mode exists, use the smallest font size as baseline
            # This helps identify larger fonts as headings
            return min(font_sizes)

    def _determine_heading_level(
        self,
        text_block: TextBlock,
        baseline_font_size: float
    ) -> Optional[int]:
        """
        Determine if a text block should be a heading and what level.
        
        Returns:
            int: Heading level (1-6) or None if not a heading
        """
        if not text_block.font_size:
            return None

        # Check content length constraints
        content_length = len(text_block.content.strip())
        if (content_length < self.config.min_heading_length or
            content_length > self.config.max_heading_length):
            return None

        # Calculate size ratio relative to baseline
        size_ratio = text_block.font_size / baseline_font_size

        # Add bonus for style characteristics
        style_bonus = 0.0
        if self._is_likely_bold(text_block):
            style_bonus += self.config.bold_weight

        adjusted_ratio = size_ratio + style_bonus

        # Check if meets minimum size difference threshold
        if text_block.font_size - baseline_font_size < self.config.min_size_difference:
            return None

        # Map ratio to heading levels (H1-H6) - check from highest level down
        for level in range(1, 7):  # H1 to H6
            required_ratio = self.config.level_multipliers[level]
            if adjusted_ratio >= required_ratio:
                return level

        # If it's significantly larger than baseline but doesn't fit standard levels,
        # make it the smallest heading (H6)
        if adjusted_ratio > 1.0:  # Some minimum threshold
            return 6

        return None

    def _is_likely_bold(self, text_block: TextBlock) -> bool:
        """Determine if text block is likely bold formatted."""
        # This is a simple heuristic - in a real implementation,
        # we would get this information from the PDF parser
        return getattr(text_block, 'is_bold', False)
