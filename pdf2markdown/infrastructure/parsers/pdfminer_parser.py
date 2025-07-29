"""PDFMiner-based parser implementation following Strategy pattern."""

import logging
import re
from pathlib import Path
from typing import Dict
from typing import Iterator
from typing import List
from typing import Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar
from pdfminer.layout import LTTextBox
from pdfminer.layout import LTTextContainer
from pdfminer.layout import LTTextLine

from pdf2markdown.domain.interfaces import PdfParserStrategy
from pdf2markdown.domain.interfaces import TextElement
from pdf2markdown.domain.models import Document
from pdf2markdown.domain.models import TextBlock


class PdfMinerParser(PdfParserStrategy):
    """
    PDFMiner-based implementation of PDF parsing strategy.
    
    Follows:
    - Strategy Pattern: Concrete implementation of PdfParserStrategy
    - Single Responsibility: Only responsible for PDF text extraction
    - Open/Closed: Can be extended without modifying existing code
    """

    def __init__(self) -> None:
        """Initialize parser with logging."""
        self.logger = logging.getLogger(__name__)

    def extract_text_elements(self, file_path: Path) -> Iterator[TextElement]:
        """
        Extract text elements from PDF with detailed formatting information.
        
        This method streams text elements to avoid loading entire document into memory.
        
        Args:
            file_path: Path to the PDF file
            
        Yields:
            TextElement: Text elements with formatting metadata
            
        Raises:
            ValueError: If file cannot be parsed
            IOError: If file cannot be read
        """
        try:
            if not file_path.exists():
                raise OSError(f"File not found: {file_path}")

            if not file_path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {file_path}")

            page_number = 1

            for page_layout in extract_pages(str(file_path)):
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        yield from self._extract_from_text_container(
                            element, page_number
                        )
                page_number += 1

        except Exception as e:
            self.logger.error(f"Error parsing PDF {file_path}: {e}")
            if isinstance(e, (IOError, ValueError)):
                raise
            raise ValueError(f"Failed to parse PDF: {e}") from e

    def _extract_from_text_container(
        self,
        container: LTTextContainer,
        page_number: int
    ) -> Iterator[TextElement]:
        """Extract text elements from a text container with formatting."""
        # Extract line-by-line to preserve positioning information
        for line in container:
            if isinstance(line, (LTTextBox, LTTextLine)):
                yield from self._extract_from_text_line(line, page_number)
            elif isinstance(line, LTTextContainer):
                # Recursively handle nested containers
                yield from self._extract_from_text_container(line, page_number)

    def _extract_from_text_line(
        self,
        line: LTTextLine,
        page_number: int
    ) -> Iterator[TextElement]:
        """Extract text elements from a single text line with precise positioning."""
        # Use line.get_text() directly to preserve spacing instead of char-by-char reconstruction
        text_content = line.get_text()

        # Still need to analyze characters for formatting information
        font_sizes = []
        font_names = []
        is_bold_chars = []
        is_italic_chars = []

        for char in line:
            if isinstance(char, LTChar):
                font_sizes.append(char.height)
                font_names.append(getattr(char, 'fontname', ''))

                # Enhanced font analysis
                font_name = getattr(char, 'fontname', '').lower()
                is_bold = self._detect_bold_formatting(font_name)
                is_italic = self._detect_italic_formatting(font_name)

                is_bold_chars.append(is_bold)
                is_italic_chars.append(is_italic)

        if text_content.strip():
            # Enhanced formatting analysis for the line
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
            dominant_font = max(set(font_names), key=font_names.count) if font_names else None

            # Use weighted bold/italic detection (70% threshold for mixed formatting)
            is_bold = sum(is_bold_chars) > len(is_bold_chars) * 0.3 if is_bold_chars else False
            is_italic = sum(is_italic_chars) > len(is_italic_chars) * 0.3 if is_italic_chars else False

            # Additional style analysis
            style_metadata = self._analyze_text_style(text_content, font_names, font_sizes)

            # Use line-level positioning for more accurate coordinates
            line_x = line.x0  # Left edge of the line
            line_y = line.y1  # Top edge of the line
            line_height = line.height

            # Create enhanced TextElement with style metadata
            element = TextElement(
                content=text_content.rstrip('\n'),  # Only strip trailing newlines, preserve internal spaces
                font_size=avg_font_size,
                font_name=dominant_font,
                is_bold=is_bold,
                is_italic=is_italic,
                x_position=line_x,
                y_position=line_y,
                page_number=page_number
            )

            # Add style metadata as attributes (maintaining interface compatibility)
            if hasattr(element, '__dict__'):
                element.__dict__.update(style_metadata)

            yield element

    def extract_line_elements(self, file_path: Path) -> Iterator[Tuple[str, float, float, float, int]]:
        """Extract line-level text elements with precise positioning for paragraph detection.
        
        Returns:
            Iterator of tuples: (text, x_position, y_position, height, page_number)
        """
        try:
            if not file_path.exists():
                raise OSError(f"File not found: {file_path}")

            if not file_path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {file_path}")

            page_number = 1
            for page_layout in extract_pages(str(file_path)):
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        yield from self._extract_lines_from_container(element, page_number)
                page_number += 1

        except Exception as e:
            self.logger.error(f"Error extracting line elements from PDF {file_path}: {e}")
            if isinstance(e, (IOError, ValueError)):
                raise
            raise ValueError(f"Failed to extract line elements: {e}") from e

    def _extract_lines_from_container(
        self,
        container: LTTextContainer,
        page_number: int
    ) -> Iterator[Tuple[str, float, float, float, int]]:
        """Extract individual lines from a text container."""
        for line in container:
            if isinstance(line, LTTextLine):
                text_content = line.get_text().strip()
                if text_content:
                    yield (
                        text_content,
                        line.x0,     # Left edge
                        line.y1,     # Top edge (PDFMiner uses bottom-up coordinates)
                        line.height,  # Line height
                        page_number
                    )
            elif isinstance(line, LTTextContainer):
                # Recursively handle nested containers
                yield from self._extract_lines_from_container(line, page_number)

    def parse_document(self, file_path: Path) -> Document:
        """
        Parse PDF file into a Document model with basic structure detection.
        
        This method creates a Document and populates it with TextBlocks.
        Heading detection will be handled by a separate service.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Document: Parsed document with basic text blocks
            
        Raises:
            ValueError: If file cannot be parsed
            IOError: If file cannot be read
        """
        try:
            document = Document()

            # Extract basic metadata from file
            document.metadata = {
                'source_file': str(file_path),
                'parser': 'pdfminer'
            }

            # Extract text elements and create basic text blocks
            for text_element in self.extract_text_elements(file_path):
                # Skip very short elements (likely noise)
                if len(text_element.content.strip()) < 3:
                    continue

                # Create basic text block - heading detection will be done separately
                text_block = TextBlock(
                    content=text_element.content,
                    font_size=text_element.font_size
                )
                document.add_block(text_block)

            self.logger.info(f"Parsed {len(document.blocks)} text blocks from {file_path}")
            return document

        except Exception as e:
            self.logger.error(f"Error creating document from {file_path}: {e}")
            raise

    def _detect_bold_formatting(self, font_name: str) -> bool:
        """
        Enhanced bold detection using comprehensive font name analysis.
        
        Args:
            font_name: Font name from PDF character
            
        Returns:
            bool: True if font appears to be bold
        """
        if not font_name:
            return False

        font_name_lower = font_name.lower()

        # Primary bold indicators
        bold_indicators = [
            'bold', 'black', 'heavy', 'extrabold', 'ultrabold',
            'semibold', 'demibold', 'medium', 'thick'
        ]

        # Font family specific indicators
        family_bold_patterns = [
            r'.*-b$',  # Font names ending with -B
            r'.*-bold$',  # Font names ending with -Bold
            r'.*bold.*',  # Any font with 'bold' in name
            r'.*black.*',  # Any font with 'black' in name
            r'.*heavy.*',  # Any font with 'heavy' in name
        ]

        # Check primary indicators
        for indicator in bold_indicators:
            if indicator in font_name_lower:
                return True

        # Check pattern-based indicators
        for pattern in family_bold_patterns:
            if re.match(pattern, font_name_lower):
                return True

        return False

    def _detect_italic_formatting(self, font_name: str) -> bool:
        """
        Enhanced italic detection using comprehensive font name analysis.
        
        Args:
            font_name: Font name from PDF character
            
        Returns:
            bool: True if font appears to be italic
        """
        if not font_name:
            return False

        font_name_lower = font_name.lower()

        # Primary italic indicators
        italic_indicators = [
            'italic', 'oblique', 'slanted', 'cursive'
        ]

        # Font family specific patterns
        italic_patterns = [
            r'.*-i$',  # Font names ending with -I
            r'.*-italic$',  # Font names ending with -Italic
            r'.*italic.*',  # Any font with 'italic' in name
            r'.*oblique.*',  # Any font with 'oblique' in name
        ]

        # Check primary indicators
        for indicator in italic_indicators:
            if indicator in font_name_lower:
                return True

        # Check pattern-based indicators
        for pattern in italic_patterns:
            if re.match(pattern, font_name_lower):
                return True

        return False

    def _analyze_text_style(self, text_content: str, font_names: List[str], font_sizes: List[float]) -> Dict:
        """
        Analyze additional text style characteristics.
        
        Args:
            text_content: Text content of the line
            font_names: List of font names in the line
            font_sizes: List of font sizes in the line
            
        Returns:
            Dict: Style metadata including formatting patterns
        """
        style_metadata = {}

        # Analyze text case patterns
        stripped_text = text_content.strip()
        if stripped_text:
            style_metadata['is_all_caps'] = stripped_text.isupper()
            style_metadata['is_title_case'] = stripped_text.istitle()
            style_metadata['has_mixed_case'] = not (stripped_text.isupper() or stripped_text.islower())

        # Analyze font consistency
        unique_fonts = set(font_names) if font_names else set()
        style_metadata['font_consistency'] = len(unique_fonts) <= 1
        style_metadata['font_variety_count'] = len(unique_fonts)

        # Analyze size consistency
        if font_sizes:
            size_variance = max(font_sizes) - min(font_sizes) if len(font_sizes) > 1 else 0.0
            style_metadata['size_consistency'] = size_variance < 1.0
            style_metadata['size_variance'] = size_variance

        # Analyze punctuation patterns (headings often lack terminal punctuation)
        style_metadata['has_terminal_punctuation'] = stripped_text.endswith(('.', '!', '?', ':', ';'))

        # Analyze word count (headings are typically shorter)
        style_metadata['word_count'] = len(stripped_text.split())

        return style_metadata
