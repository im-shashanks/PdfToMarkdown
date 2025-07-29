"""Paragraph detection service implementing text flow analysis."""

from statistics import mean
from statistics import stdev
from typing import Dict
from typing import List

from pdf2markdown.domain.interfaces.paragraph_detector import ParagraphDetectorInterface
from pdf2markdown.domain.models.document import Block
from pdf2markdown.domain.models.document import Document
from pdf2markdown.domain.models.document import Line
from pdf2markdown.domain.models.document import Paragraph
from pdf2markdown.domain.models.document import TextAlignment
from pdf2markdown.domain.models.document import TextBlock
from pdf2markdown.domain.models.document import TextFlow


class ParagraphDetector(ParagraphDetectorInterface):
    """
    Service for detecting paragraphs and analyzing text flow.
    
    Follows Single Responsibility Principle - focused on paragraph detection logic.
    Uses Strategy pattern for different text flow analysis algorithms.
    """

    def __init__(
        self,
        line_spacing_threshold: float = 1.8,  # More conservative
        min_paragraph_lines: int = 1,
        indentation_threshold: float = 10.0,
        alignment_tolerance: float = 5.0,
        content_aware_merging: bool = True  # Enable content-aware merging
    ):
        """
        Initialize paragraph detector with configuration.
        
        Args:
            line_spacing_threshold: Multiplier for detecting paragraph breaks
            min_paragraph_lines: Minimum lines required for a paragraph
            indentation_threshold: Minimum x-position difference for indentation
            alignment_tolerance: Tolerance for alignment detection
        """
        self.line_spacing_threshold = line_spacing_threshold
        self.min_paragraph_lines = min_paragraph_lines
        self.indentation_threshold = indentation_threshold
        self.alignment_tolerance = alignment_tolerance
        self.content_aware_merging = content_aware_merging

    def detect_paragraphs_in_document(self, document: Document) -> Document:
        """
        Enhanced paragraph detection with content-aware processing.
        
        Preserves document structure while intelligently merging text blocks
        based on content patterns, formatting, and semantic analysis.
        """
        if not document.blocks:
            return document

        # Group consecutive text blocks for batch processing
        block_groups = self._group_consecutive_text_blocks(document.blocks)
        new_blocks: List[Block] = []

        for group in block_groups:
            if self._is_text_block_group(group):
                # Process text block group with enhanced logic
                processed_paragraphs = self._process_text_block_group(group)
                new_blocks.extend(processed_paragraphs)
            else:
                # Preserve non-text blocks as-is
                new_blocks.extend(group)

        return Document(
            title=document.title,
            blocks=new_blocks,
            metadata=document.metadata
        )

    def convert_text_block_to_paragraph(self, text_block: TextBlock) -> Paragraph:
        """
        Convert a TextBlock to a Paragraph with proper line analysis.
        
        Returns None for empty or whitespace-only content.
        """
        # Check for empty or whitespace-only content
        if not text_block.content.strip():
            return Paragraph(lines=[], font_size=text_block.font_size)

        # Split content into lines (simplified for now)
        lines_text = text_block.content.split('\n')
        lines: List[Line] = []

        # Create Line objects with simulated positioning
        for i, line_text in enumerate(lines_text):
            if line_text.strip():  # Skip empty lines
                # Detect indentation from original text
                x_offset = len(line_text) - len(line_text.lstrip())
                x_position = 50.0 + (x_offset * 2.0)  # 2 points per space

                lines.append(Line(
                    text=line_text,  # Keep original text with indentation
                    y_position=100.0 - (i * 15.0),  # Simulated y-position
                    x_position=x_position,
                    height=12.0,  # Simulated line height
                    font_size=text_block.font_size
                ))

        # Analyze text flow
        text_flow = self._create_text_flow_from_lines(lines)

        # Detect if this is a continuation
        paragraph = Paragraph(
            lines=lines,
            text_flow=text_flow,
            font_size=text_block.font_size,
            is_continuation=self._is_paragraph_continuation_from_text(text_block.content)
        )

        return paragraph

    def merge_continuous_paragraphs(self, paragraphs: List[Paragraph]) -> List[Paragraph]:
        """
        Enhanced paragraph merging with content-aware logic.
        
        Uses semantic analysis, formatting patterns, and content structure
        to determine appropriate paragraph boundaries.
        """
        if not paragraphs:
            return []

        if not self.content_aware_merging:
            return paragraphs  # Skip merging if disabled

        merged: List[Paragraph] = []
        current_paragraph = paragraphs[0]

        for next_paragraph in paragraphs[1:]:
            if self._should_merge_paragraphs_enhanced(current_paragraph, next_paragraph):
                # Merge paragraphs with improved logic
                current_paragraph.merge_with(next_paragraph)
            else:
                # Start new paragraph
                merged.append(current_paragraph)
                current_paragraph = next_paragraph

        # Add the last paragraph
        merged.append(current_paragraph)

        return merged

    def _analyze_line_spacing(self, lines: List[Line]) -> Dict:
        """Analyze vertical spacing between lines to detect paragraph breaks."""
        if len(lines) < 2:
            return {
                "average_spacing": 0.0,
                "spacing_consistency": 1.0,
                "paragraph_breaks": []
            }

        spacings = []
        for i in range(len(lines) - 1):
            spacing = lines[i].vertical_spacing_to(lines[i + 1])
            spacings.append(spacing)

        average_spacing = mean(spacings)
        spacing_std = stdev(spacings) if len(spacings) > 1 else 0.0
        consistency = 1.0 - (spacing_std / (average_spacing + 1.0))  # Avoid division by zero

        # Detect paragraph breaks (spacing significantly larger than average)
        paragraph_breaks = []
        threshold = average_spacing * self.line_spacing_threshold

        for i, spacing in enumerate(spacings):
            if spacing > threshold:
                paragraph_breaks.append(i + 1)  # Index of line starting new paragraph

        return {
            "average_spacing": average_spacing,
            "spacing_consistency": consistency,
            "paragraph_breaks": paragraph_breaks
        }

    def _detect_text_alignment(self, lines: List[Line]) -> TextAlignment:
        """Detect text alignment from line positions."""
        if not lines:
            return TextAlignment.LEFT

        x_positions = [line.x_position for line in lines]

        # Check for consistent left alignment
        left_aligned = all(
            abs(pos - x_positions[0]) <= self.alignment_tolerance
            for pos in x_positions
        )

        if left_aligned:
            return TextAlignment.LEFT

        # Check for center alignment (positions vary around a center point)
        x_mean = mean(x_positions)
        center_variance = sum(abs(pos - x_mean) for pos in x_positions) / len(x_positions)

        if center_variance <= self.alignment_tolerance * 2:
            return TextAlignment.CENTER

        # Default to left if unclear
        return TextAlignment.LEFT

    def _detect_indentation(self, lines: List[Line]) -> float:
        """Detect indentation amount from line positions."""
        if not lines:
            return 0.0

        min_x = min(line.x_position for line in lines)
        # Indentation is relative to some baseline (simplified)
        baseline_x = 50.0  # Assumed baseline

        return max(0.0, min_x - baseline_x)

    def _create_text_flow_from_lines(self, lines: List[Line]) -> TextFlow:
        """Create TextFlow object from line analysis."""
        if not lines:
            return TextFlow()

        alignment = self._detect_text_alignment(lines)
        indentation = self._detect_indentation(lines)
        average_height = mean(line.height for line in lines)

        # Calculate line spacing (simplified)
        if len(lines) > 1:
            spacings = []
            for i in range(len(lines) - 1):
                spacing = lines[i].vertical_spacing_to(lines[i + 1])
                spacings.append(spacing / average_height)  # Normalize by line height
            line_spacing = mean(spacings) if spacings else 1.0
        else:
            line_spacing = 1.0

        return TextFlow(
            alignment=alignment,
            line_spacing=line_spacing,
            indentation=indentation,
            average_line_height=average_height
        )

    def _is_paragraph_continuation(self, paragraph: Paragraph) -> bool:
        """Check if paragraph is a continuation of previous text."""
        if not paragraph.lines:
            return False

        first_line = paragraph.lines[0].text.strip()
        return self._is_paragraph_continuation_from_text(first_line)

    def _is_paragraph_continuation_from_text(self, text: str) -> bool:
        """Check if text appears to be a continuation based on content."""
        if not text:
            return False

        text = text.strip()

        # Continuation indicators:
        # 1. Starts with lowercase letter (not quoted)
        # 2. Starts with specific continuation words

        continuation_words = {
            'and', 'but', 'or', 'so', 'for', 'yet', 'nor',
            'however', 'therefore', 'moreover', 'furthermore',
            'nevertheless', 'consequently', 'thus', 'hence'
        }

        first_word = text.split()[0].lower() if text.split() else ""

        # Check if starts with lowercase (excluding quoted text and numbers)
        if (text[0].islower() and
            not text.startswith('"') and
            not text.startswith("'") and
            not text[0].isdigit()):
            return True

        # Check for continuation words
        return first_word in continuation_words

    def _should_merge_paragraphs(self, _para1: Paragraph, para2: Paragraph) -> bool:
        """Determine if two paragraphs should be merged."""
        # Only merge if second paragraph is explicitly marked as continuation
        # OR if it starts with continuation indicators
        return (para2.is_continuation or
                self._is_paragraph_continuation(para2))

    def _split_lines_at_paragraph_breaks(
        self,
        lines: List[Line],
        break_indices: List[int]
    ) -> List[Paragraph]:
        """Split lines into separate paragraphs at detected break points."""
        if not break_indices:
            # No breaks, create single paragraph
            return [Paragraph(lines=lines)]

        paragraphs = []
        start_idx = 0

        for break_idx in break_indices:
            if start_idx < break_idx:
                paragraph_lines = lines[start_idx:break_idx]
                if paragraph_lines:  # Only create paragraph if it has lines
                    text_flow = self._create_text_flow_from_lines(paragraph_lines)
                    paragraphs.append(Paragraph(
                        lines=paragraph_lines,
                        text_flow=text_flow
                    ))
            start_idx = break_idx

        # Add remaining lines as final paragraph
        if start_idx < len(lines):
            remaining_lines = lines[start_idx:]
            if remaining_lines:
                text_flow = self._create_text_flow_from_lines(remaining_lines)
                paragraphs.append(Paragraph(
                    lines=remaining_lines,
                    text_flow=text_flow
                ))

        return paragraphs

    def detect_paragraphs_from_pdf(self, file_path) -> Document:
        """
        Detect paragraphs directly from PDF file using line-level analysis.
        
        This method provides more accurate paragraph detection by working
        directly with PDF coordinate data rather than pre-processed text blocks.
        """
        from pathlib import Path as PathlibPath

        try:
            parser = PdfMinerParser()
            lines_data = list(parser.extract_line_elements(PathlibPath(file_path)))

            if not lines_data:
                return Document(metadata={'source_file': str(file_path)})

            # Group lines by page and sort by vertical position
            pages_lines = {}
            for text, x_pos, y_pos, height, page_num in lines_data:
                if page_num not in pages_lines:
                    pages_lines[page_num] = []
                pages_lines[page_num].append((text, x_pos, y_pos, height))

            # Process each page separately
            document = Document(metadata={'source_file': str(file_path)})

            for page_num in sorted(pages_lines.keys()):
                page_lines_data = pages_lines[page_num]
                # Sort by y-position (descending, as PDF coordinates are bottom-up)
                page_lines_data.sort(key=lambda x: x[2], reverse=True)

                # Create Line objects from coordinate data
                page_lines = []
                for text, x_pos, y_pos, height in page_lines_data:
                    if text.strip():
                        page_lines.append(Line(
                            text=text,
                            x_position=x_pos,
                            y_position=y_pos,
                            height=height
                        ))

                # Detect paragraph boundaries using spacing analysis
                spacing_analysis = self._analyze_line_spacing(page_lines)
                paragraph_breaks = spacing_analysis.get('paragraph_breaks', [])

                # Split lines into paragraphs
                paragraphs = self._split_lines_at_paragraph_breaks(
                    page_lines, paragraph_breaks
                )

                # Add paragraphs to document
                for paragraph in paragraphs:
                    if not paragraph.is_empty():
                        document.add_block(paragraph)

            return document

        except Exception as e:
            # Fallback to basic document structure
            return Document(metadata={'source_file': str(file_path), 'error': str(e)})

    def _group_consecutive_text_blocks(self, blocks: List[Block]) -> List[List[Block]]:
        """
        Group consecutive text blocks for batch processing.
        
        Returns:
            List of block groups, where each group is either consecutive text blocks
            or a single non-text block.
        """
        if not blocks:
            return []

        groups = []
        current_group = []

        for block in blocks:
            if isinstance(block, TextBlock):
                current_group.append(block)
            else:
                # Non-text block: finish current group and start new one
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([block])  # Single non-text block group

        # Add any remaining text blocks
        if current_group:
            groups.append(current_group)

        return groups

    def _is_text_block_group(self, group: List[Block]) -> bool:
        """Check if a group consists of text blocks."""
        return group and isinstance(group[0], TextBlock)

    def _process_text_block_group(self, text_blocks: List[TextBlock]) -> List[Block]:
        """
        Process a group of consecutive text blocks with enhanced logic.
        
        Args:
            text_blocks: List of consecutive text blocks
            
        Returns:
            List of processed paragraph blocks
        """
        if not text_blocks:
            return []

        # Convert text blocks to paragraphs
        paragraphs = []
        for text_block in text_blocks:
            paragraph = self.convert_text_block_to_paragraph(text_block)
            if not paragraph.is_empty():
                paragraphs.append(paragraph)

        if not paragraphs:
            return []

        # Apply enhanced merging logic
        merged_paragraphs = self.merge_continuous_paragraphs(paragraphs)

        # Filter out empty paragraphs after merging
        return [p for p in merged_paragraphs if not p.is_empty()]

    def _should_merge_paragraphs_enhanced(self, para1: Paragraph, para2: Paragraph) -> bool:
        """
        Enhanced paragraph merging logic with multiple criteria.
        
        Args:
            para1: First paragraph
            para2: Second paragraph
            
        Returns:
            bool: True if paragraphs should be merged
        """
        # Get content for analysis
        content1 = para1.content.strip()
        content2 = para2.content.strip()

        if not content1 or not content2:
            return False

        # CRITICAL: Never merge resume section headers
        if (self._is_resume_section_header(content1) or
            self._is_resume_section_header(content2)):
            return False

        # Never merge if either looks like a major section header
        if (self._is_section_header(content1) or self._is_section_header(content2)):
            return False

        # Never merge across significant font size differences (indicates hierarchy)
        if (hasattr(para1, 'font_size') and hasattr(para2, 'font_size') and
            para1.font_size is not None and para2.font_size is not None):
            if abs(para1.font_size - para2.font_size) > 0.5:  # Even smaller differences
                return False

        # Never merge list items with non-list content
        if (self._is_list_item(content1) and not self._is_list_item(content2)) or \
           (self._is_list_item(content2) and not self._is_list_item(content1)):
            return False

        # Only merge list items if they're the same type
        if self._is_list_item(content1) and self._is_list_item(content2):
            return self._is_same_list_type(content1, content2)

        # Check for explicit continuation markers (only clear cases)
        if self._is_explicit_continuation(content2):
            return True

        # Check for natural sentence continuation (very conservative)
        if self._suggests_sentence_continuation(content1, content2):
            return True

        # Default: DON'T merge (very conservative for resume structure)
        return False

    def _is_explicit_continuation(self, content: str) -> bool:
        """
        Check for explicit continuation indicators.
        
        Args:
            content: Text content to check
            
        Returns:
            bool: True if content appears to be a continuation
        """
        content_stripped = content.strip()
        content_lower = content_stripped.lower()

        # Starts with lowercase (excluding quoted text, numbers, proper nouns)
        if (content_stripped and content_stripped[0].islower() and
            not content_stripped.startswith('"') and not content_stripped.startswith("'") and
            not any(content_lower.startswith(word) for word in ['i', 'a'])):
            return True

        # Explicit continuation words
        continuation_starters = {
            'and', 'but', 'or', 'so', 'for', 'yet', 'nor',
            'however', 'therefore', 'moreover', 'furthermore',
            'nevertheless', 'consequently', 'thus', 'hence',
            'additionally', 'meanwhile', 'similarly'
        }

        first_word = content_lower.split()[0] if content_lower.split() else ""
        return first_word in continuation_starters

    def _is_section_header(self, content: str) -> bool:
        """
        Check if content appears to be a section header.
        
        Args:
            content: Text content to check
            
        Returns:
            bool: True if content appears to be a section header
        """
        content = content.strip()

        # ALL CAPS sections
        if content.isupper() and 3 <= len(content) <= 50:
            return True

        # Common section keywords
        section_keywords = {
            'education', 'experience', 'skills', 'summary', 'objective',
            'background', 'qualifications', 'achievements', 'projects',
            'certifications', 'awards', 'career', 'professional',
            'employment', 'work history', 'technical skills'
        }

        content_lower = content.lower()
        if any(keyword in content_lower for keyword in section_keywords):
            return True

        # Short, title-case lines without terminal punctuation
        if (content.istitle() and len(content.split()) <= 4 and
            not content.endswith(('.', '!', '?', ':', ';'))):
            return True

        return False

    def _is_list_item(self, content: str) -> bool:
        """
        Check if content appears to be a list item.
        
        Args:
            content: Text content to check
            
        Returns:
            bool: True if content appears to be a list item
        """
        content = content.strip()

        # Bullet points
        bullet_markers = ['•', '◦', '▪', '▫', '■', '□', '○', '●', '-', '*']
        if any(content.startswith(marker) for marker in bullet_markers):
            return True

        # Numbered lists
        numbered_patterns = [
            r'^\d+\.',  # 1. 2. 3.
            r'^\d+\)',  # 1) 2) 3)
            r'^\([\da-z]\)',  # (a) (b) (1) (2)
            r'^[a-z]\.',  # a. b. c.
            r'^[A-Z]\.',  # A. B. C.
        ]

        import re
        for pattern in numbered_patterns:
            if re.match(pattern, content):
                return True

        return False

    def _is_same_list_type(self, content1: str, content2: str) -> bool:
        """
        Check if two list items are of the same type.
        
        Args:
            content1: First list item content
            content2: Second list item content
            
        Returns:
            bool: True if both items are from the same list type
        """
        import re

        # Extract list markers
        def get_list_marker(content):
            content = content.strip()

            # Bullet markers
            bullet_markers = ['•', '◦', '▪', '▫', '■', '□', '○', '●', '-', '*']
            for marker in bullet_markers:
                if content.startswith(marker):
                    return marker

            # Numbered patterns
            numbered_patterns = [
                (r'^(\d+)\.'),  # 1. 2. 3.
                (r'^(\d+)\)'),  # 1) 2) 3)
                (r'^\(([\da-z])\)'),  # (a) (b) (1) (2)
                (r'^([a-z])\.'),  # a. b. c.
                (r'^([A-Z])\.'),  # A. B. C.
            ]

            for pattern in numbered_patterns:
                match = re.match(pattern, content)
                if match:
                    return pattern  # Return pattern type, not specific number

            return None

        marker1 = get_list_marker(content1)
        marker2 = get_list_marker(content2)

        # Both must have markers and they should be the same type
        return marker1 is not None and marker2 is not None and marker1 == marker2

    def _suggests_sentence_continuation(self, content1: str, content2: str) -> bool:
        """
        Check if content suggests natural sentence continuation.
        
        Args:
            content1: First paragraph content
            content2: Second paragraph content
            
        Returns:
            bool: True if content suggests continuation
        """
        content1 = content1.strip()
        content2 = content2.strip()

        # First paragraph doesn't end with terminal punctuation
        if not content1.endswith(('.', '!', '?', ':', ';')):
            # Second paragraph starts with lowercase or continuation word
            if (content2 and content2[0].islower()) or self._is_explicit_continuation(content2):
                return True

        # Check for common continuation patterns
        if (content1.endswith(',') and content2 and
            not content2[0].isupper() and not self._is_section_header(content2)):
            return True

        return False

    def _is_resume_section_header(self, content: str) -> bool:
        """
        Detect resume section headers to prevent merging.
        
        Returns:
            bool: True if content is a resume section header
        """
        content_clean = content.strip().upper()

        # Major resume sections
        resume_sections = {
            'PROFESSIONAL SUMMARY', 'EXECUTIVE SUMMARY', 'SUMMARY', 'OBJECTIVE',
            'EXPERIENCE', 'WORK EXPERIENCE', 'CAREER EXPERIENCE', 'EMPLOYMENT',
            'EDUCATION', 'EDUCATIONAL BACKGROUND', 'ACADEMIC BACKGROUND',
            'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'KEY SKILLS',
            'CERTIFICATIONS', 'CERTIFICATES', 'AWARDS', 'HONORS',
            'PROJECTS', 'PUBLICATIONS', 'RESEARCH', 'REFERENCES'
        }

        # Check for exact matches
        if content_clean in resume_sections:
            return True

        # Check for single word sections
        single_words = {'SUMMARY', 'OBJECTIVE', 'EXPERIENCE', 'EDUCATION',
                       'SKILLS', 'CERTIFICATIONS', 'AWARDS', 'PROJECTS', 'REFERENCES'}
        if content_clean in single_words:
            return True

        # Check if content starts with a major section keyword
        for section in resume_sections:
            if content_clean.startswith(section) and len(content_clean) <= len(section) + 10:
                return True

        return False
