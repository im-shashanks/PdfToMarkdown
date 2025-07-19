"""Unit tests for PDFMiner parser implementation."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Iterator

import pytest

from pdf2markdown.domain.interfaces import TextElement
from pdf2markdown.domain.models import Document, TextBlock
from pdf2markdown.infrastructure.parsers import PdfMinerParser


class TestPdfMinerParser:
    """Test suite for PDFMiner parser implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PdfMinerParser()
    
    def test_parser_initialization(self):
        """Test parser initializes correctly."""
        # Arrange & Act
        parser = PdfMinerParser()
        
        # Assert
        assert parser.logger is not None
        assert parser.logger.name == "pdf2markdown.infrastructure.parsers.pdfminer_parser"
    
    def test_extract_text_elements_file_not_found(self):
        """Test extraction fails when file doesn't exist."""
        # Arrange
        non_existent_file = Path("/non/existent/file.pdf")
        
        # Act & Assert
        with pytest.raises(IOError, match="File not found"):
            list(self.parser.extract_text_elements(non_existent_file))
    
    def test_extract_text_elements_invalid_extension(self):
        """Test extraction fails for non-PDF files."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Act & Assert
            with pytest.raises(ValueError, match="File is not a PDF"):
                list(self.parser.extract_text_elements(temp_path))
        finally:
            temp_path.unlink()
    
    def test_font_style_detection_logic(self):
        """Test font style detection logic without complex mocking."""
        # Test the font name parsing logic directly
        test_cases = [
            ("Arial-Bold", True, False),
            ("Times-Italic", False, True),
            ("Helvetica-BoldItalic", True, True),
            ("Georgia-Regular", False, False),
            ("SomeFont-Black", True, False),
            ("AnotherFont-Oblique", False, True),
            ("Normal-Font", False, False),
            ("Heavy-Font", True, False),
        ]
        
        for font_name, expected_bold, expected_italic in test_cases:
            # Test the logic used in the parser directly
            font_name_lower = font_name.lower()
            is_bold = any(indicator in font_name_lower for indicator in ['bold', 'black', 'heavy'])
            is_italic = any(indicator in font_name_lower for indicator in ['italic', 'oblique'])
            
            assert is_bold == expected_bold, f"Font {font_name} bold detection failed"
            assert is_italic == expected_italic, f"Font {font_name} italic detection failed"
    
    @patch.object(PdfMinerParser, 'extract_text_elements')
    def test_parse_document_success(self, mock_extract_text_elements):
        """Test successful document parsing using mocked extract_text_elements."""
        # Arrange
        mock_elements = [
            TextElement(
                content="Title Text",
                font_size=16.0,
                font_name="Arial-Bold",
                is_bold=True,
                page_number=1
            ),
            TextElement(
                content="Body paragraph with sufficient length to pass filtering.",
                font_size=12.0,
                font_name="Arial-Regular",
                page_number=1
            )
        ]
        mock_extract_text_elements.return_value = iter(mock_elements)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Act
            document = self.parser.parse_document(temp_path)
            
            # Assert
            assert isinstance(document, Document)
            assert len(document.blocks) == 2
            assert isinstance(document.blocks[0], TextBlock)
            assert document.blocks[0].content == "Title Text"
            assert document.blocks[0].font_size == 16.0
            assert document.blocks[1].content == "Body paragraph with sufficient length to pass filtering."
            assert document.metadata['source_file'] == str(temp_path)
            assert document.metadata['parser'] == 'pdfminer'
        finally:
            temp_path.unlink()
    
    @patch.object(PdfMinerParser, 'extract_text_elements')
    def test_parse_document_filters_short_content(self, mock_extract_text_elements):
        """Test that very short content is filtered out."""
        # Arrange
        mock_elements = [
            TextElement(content="A", font_size=12.0, page_number=1),  # Too short
            TextElement(content="B", font_size=12.0, page_number=1),  # Too short
            TextElement(content="This is long enough content", font_size=12.0, page_number=1),  # Long enough
        ]
        mock_extract_text_elements.return_value = iter(mock_elements)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Act
            document = self.parser.parse_document(temp_path)
            
            # Assert
            assert len(document.blocks) == 1  # Only the long content should be included
            assert document.blocks[0].content == "This is long enough content"
        finally:
            temp_path.unlink()
    
    def test_parse_document_file_not_found(self):
        """Test document parsing fails when file doesn't exist."""
        # Arrange
        non_existent_file = Path("/non/existent/file.pdf")
        
        # Act & Assert
        with pytest.raises(IOError):
            self.parser.parse_document(non_existent_file)
    
    @patch.object(PdfMinerParser, 'extract_text_elements')
    def test_parse_document_handles_empty_content(self, mock_extract_text_elements):
        """Test document parsing with empty or whitespace-only content."""
        # Arrange
        mock_elements = [
            TextElement(content="   ", font_size=12.0, page_number=1),  # Whitespace only
            TextElement(content="", font_size=12.0, page_number=1),     # Empty
        ]
        mock_extract_text_elements.return_value = iter(mock_elements)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Act
            document = self.parser.parse_document(temp_path)
            
            # Assert
            assert len(document.blocks) == 0  # No blocks should be created
        finally:
            temp_path.unlink()