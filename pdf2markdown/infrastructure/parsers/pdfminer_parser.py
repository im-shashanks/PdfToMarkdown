"""PDFMiner-based parser implementation following Strategy pattern."""

import logging
from pathlib import Path
from typing import Iterator

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
        text_content = ""
        font_sizes = []
        font_names = []
        is_bold_chars = []
        is_italic_chars = []
        x_positions = []
        y_positions = []

        for line in container:
            if isinstance(line, (LTTextBox, LTTextLine)):
                for char in line:
                    if isinstance(char, LTChar):
                        text_content += char.get_text()
                        font_sizes.append(char.height)
                        font_names.append(getattr(char, 'fontname', ''))

                        # Detect bold and italic from font name
                        font_name = getattr(char, 'fontname', '').lower()
                        is_bold = any(indicator in font_name for indicator in ['bold', 'black', 'heavy'])
                        is_italic = any(indicator in font_name for indicator in ['italic', 'oblique'])

                        is_bold_chars.append(is_bold)
                        is_italic_chars.append(is_italic)
                        x_positions.append(char.x0)
                        y_positions.append(char.y0)

        if text_content.strip():
            # Calculate dominant formatting for the entire text element
            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
            dominant_font = max(set(font_names), key=font_names.count) if font_names else None
            is_bold = sum(is_bold_chars) > len(is_bold_chars) / 2 if is_bold_chars else False
            is_italic = sum(is_italic_chars) > len(is_italic_chars) / 2 if is_italic_chars else False
            avg_x = sum(x_positions) / len(x_positions) if x_positions else 0.0
            avg_y = sum(y_positions) / len(y_positions) if y_positions else 0.0

            yield TextElement(
                content=text_content.strip(),
                font_size=avg_font_size,
                font_name=dominant_font,
                is_bold=is_bold,
                is_italic=is_italic,
                x_position=avg_x,
                y_position=avg_y,
                page_number=page_number
            )

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
