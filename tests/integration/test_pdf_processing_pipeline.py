"""Integration tests for the complete PDF processing pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pdf2markdown.domain.interfaces import TextElement
from pdf2markdown.domain.models import Document, Heading, TextBlock
from pdf2markdown.domain.services import HeadingDetector
from pdf2markdown.infrastructure.formatters import MarkdownFormatter
from pdf2markdown.infrastructure.parsers import PdfMinerParser


class TestPdfProcessingPipeline:
    """Integration tests for the complete PDF to Markdown pipeline."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PdfMinerParser()
        self.heading_detector = HeadingDetector()
        self.formatter = MarkdownFormatter()
    
    @patch.object(PdfMinerParser, 'extract_text_elements')
    def test_complete_pipeline_simple_document(self, mock_extract_text_elements):
        """Test the complete pipeline with a simple document."""
        # Arrange
        mock_elements = [
            TextElement(content="John Doe", font_size=24.0, page_number=1),           # H1: Name
            TextElement(content="This is the introduction paragraph.", font_size=12.0, page_number=1),
            TextElement(content="EXPERIENCE", font_size=21.6, page_number=1),         # H2: Major section
            TextElement(content="Content of experience section.", font_size=12.0, page_number=1),
            TextElement(content="EDUCATION", font_size=21.6, page_number=1),          # H2: Major section
            TextElement(content="Educational background details.", font_size=12.0, page_number=1),
        ]
        mock_extract_text_elements.return_value = iter(mock_elements)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as input_file:
            input_path = Path(input_file.name)
        
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as output_file:
            output_path = Path(output_file.name)
        
        try:
            # Act - Execute the complete pipeline
            # Step 1: Parse PDF
            document = self.parser.parse_document(input_path)
            
            # Step 2: Detect headings
            document_with_headings = self.heading_detector.detect_headings_in_document(document)
            
            # Step 3: Format to Markdown
            self.formatter.format_to_file(document_with_headings, str(output_path))
            
            # Assert - Verify the output
            with open(output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Check that headings were detected and formatted correctly
            assert "# John Doe" in markdown_content
            assert "## EXPERIENCE" in markdown_content
            assert "## EDUCATION" in markdown_content
            assert "This is the introduction paragraph." in markdown_content
            assert "Content of experience section." in markdown_content
            assert "Educational background details." in markdown_content
            
            # Verify structure
            lines = markdown_content.strip().split('\n')
            assert lines[0] == "# John Doe"
            assert "## EXPERIENCE" in lines
            assert "## EDUCATION" in lines
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    @patch.object(PdfMinerParser, 'extract_text_elements')
    def test_pipeline_with_multiple_heading_levels(self, mock_extract_text_elements):
        """Test pipeline with multiple heading levels."""
        # Arrange
        mock_elements = [
            TextElement(content="Jane Smith", font_size=24.0, page_number=1),      # H1: Name
            TextElement(content="Normal text", font_size=12.0, page_number=1),     # Text
            TextElement(content="EXPERIENCE", font_size=21.6, page_number=1),      # H2: Major section
            TextElement(content="EDUCATION", font_size=18.0, page_number=1),       # H2: Major section
            TextElement(content="SKILLS", font_size=15.6, page_number=1),          # H2: Major section
            TextElement(content="Content here", font_size=12.0, page_number=1),    # Text
        ]
        mock_extract_text_elements.return_value = iter(mock_elements)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as input_file:
            input_path = Path(input_file.name)
        
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as output_file:
            output_path = Path(output_file.name)
        
        try:
            # Act
            document = self.parser.parse_document(input_path)
            document_with_headings = self.heading_detector.detect_headings_in_document(document)
            self.formatter.format_to_file(document_with_headings, str(output_path))
            
            # Assert
            with open(output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Verify heading hierarchy (resume-aware detection)
            assert "# Jane Smith" in markdown_content
            assert "## EXPERIENCE" in markdown_content
            assert "## EDUCATION" in markdown_content
            assert "## SKILLS" in markdown_content
            assert "Normal text" in markdown_content
            assert "Content here" in markdown_content
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    @patch.object(PdfMinerParser, 'extract_text_elements')
    def test_pipeline_with_no_headings(self, mock_extract_text_elements):
        """Test pipeline with document containing no headings."""
        # Arrange
        mock_elements = [
            TextElement(content="Just regular paragraph text.", font_size=12.0, page_number=1),
            TextElement(content="Another paragraph.", font_size=12.0, page_number=1),
            TextElement(content="And one more paragraph.", font_size=12.0, page_number=1),
        ]
        mock_extract_text_elements.return_value = iter(mock_elements)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as input_file:
            input_path = Path(input_file.name)
        
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as output_file:
            output_path = Path(output_file.name)
        
        try:
            # Act
            document = self.parser.parse_document(input_path)
            document_with_headings = self.heading_detector.detect_headings_in_document(document)
            self.formatter.format_to_file(document_with_headings, str(output_path))
            
            # Assert
            with open(output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Should contain text but no headings
            assert "Just regular paragraph text." in markdown_content
            assert "Another paragraph." in markdown_content
            assert "And one more paragraph." in markdown_content
            
            # Should not contain any heading markers
            assert not any(line.startswith('#') for line in markdown_content.split('\n'))
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    @patch.object(PdfMinerParser, 'extract_text_elements')
    def test_pipeline_preserves_document_metadata(self, mock_extract_text_elements):
        """Test that pipeline preserves document metadata."""
        # Arrange
        mock_elements = [
            TextElement(content="Title", font_size=18.0, page_number=1),
            TextElement(content="Content", font_size=12.0, page_number=1),
        ]
        mock_extract_text_elements.return_value = iter(mock_elements)
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as input_file:
            input_path = Path(input_file.name)
        
        try:
            # Act
            document = self.parser.parse_document(input_path)
            
            # Verify metadata was set by parser
            assert 'source_file' in document.metadata
            assert 'parser' in document.metadata
            assert document.metadata['parser'] == 'pdfminer'
            assert str(input_path) in document.metadata['source_file']
            
            # Process through heading detection
            document_with_headings = self.heading_detector.detect_headings_in_document(document)
            
            # Verify metadata is preserved
            assert document_with_headings.metadata == document.metadata
            
        finally:
            input_path.unlink()
    
    def test_pipeline_error_handling_invalid_file(self):
        """Test pipeline error handling with invalid file."""
        # Arrange
        non_existent_file = Path("/non/existent/file.pdf")
        
        # Act & Assert
        with pytest.raises(IOError):
            self.parser.parse_document(non_existent_file)