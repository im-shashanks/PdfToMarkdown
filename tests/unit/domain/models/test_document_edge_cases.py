"""Unit tests for document model edge cases and error handling."""

import pytest

from pdf2markdown.domain.models.document import (
    Document, Heading, TextBlock, Paragraph, Line, TextFlow, TextAlignment
)


class TestDocumentEdgeCases:
    """Test edge cases for document models."""
    
    def test_heading_invalid_level_too_low(self):
        """Test heading creation with level below 1."""
        with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
            Heading(level=0, content="Invalid heading")
    
    def test_heading_invalid_level_too_high(self):
        """Test heading creation with level above 6."""
        with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
            Heading(level=7, content="Invalid heading")
    
    def test_heading_empty_content(self):
        """Test heading creation with empty content."""
        with pytest.raises(ValueError, match="Heading content cannot be empty"):
            Heading(level=1, content="")
        
        with pytest.raises(ValueError, match="Heading content cannot be empty"):
            Heading(level=1, content="   ")  # Whitespace only
    
    def test_paragraph_add_line_invalid_type(self):
        """Test adding invalid type to paragraph lines."""
        paragraph = Paragraph()
        
        with pytest.raises(TypeError, match="Expected Line instance"):
            paragraph.add_line("Not a line object")
    
    def test_paragraph_merge_with_invalid_type(self):
        """Test merging paragraph with invalid type."""
        paragraph = Paragraph()
        
        with pytest.raises(TypeError, match="Expected Paragraph instance"):
            paragraph.merge_with("Not a paragraph")
    
    def test_document_add_block_invalid_type(self):
        """Test adding invalid type to document blocks."""
        document = Document()
        
        with pytest.raises(TypeError, match="Expected Block instance"):
            document.add_block("Not a block")
    
    def test_document_to_markdown_with_empty_blocks(self):
        """Test markdown generation with various empty block scenarios."""
        document = Document(title="Test Document")
        
        # Add empty paragraph
        empty_paragraph = Paragraph(lines=[])
        document.add_block(empty_paragraph)
        
        # Add paragraph with whitespace-only lines
        whitespace_lines = [
            Line("   ", y_position=100.0, x_position=50.0, height=12.0),
            Line("\t\n", y_position=85.0, x_position=50.0, height=12.0)
        ]
        whitespace_paragraph = Paragraph(lines=whitespace_lines)
        document.add_block(whitespace_paragraph)
        
        # Add valid content
        valid_paragraph = Paragraph(lines=[
            Line("Valid content", y_position=70.0, x_position=50.0, height=12.0)
        ])
        document.add_block(valid_paragraph)
        
        markdown = document.to_markdown()
        
        # Should only include title and valid content
        assert "# Test Document" in markdown
        assert "Valid content" in markdown
        # Should not include empty/whitespace content
        assert markdown.count('\n') >= 2  # Title + empty line + content
    
    def test_paragraph_bounding_box_empty_lines(self):
        """Test bounding box calculation with empty lines."""
        paragraph = Paragraph(lines=[])
        
        bbox = paragraph.get_bounding_box()
        
        assert bbox["top"] == 0.0
        assert bbox["bottom"] == 0.0
        assert bbox["left"] == 0.0
        assert bbox["right"] == 0.0
    
    def test_text_flow_is_similar_edge_cases(self):
        """Test TextFlow similarity comparison edge cases."""
        flow1 = TextFlow(alignment=TextAlignment.LEFT, line_spacing=1.0)
        flow2 = TextFlow(alignment=TextAlignment.LEFT, line_spacing=1.05)  # Very close
        flow3 = TextFlow(alignment=TextAlignment.LEFT, line_spacing=1.5)   # Different
        
        # Very small tolerance
        assert flow1.is_similar_to(flow2, spacing_tolerance=0.1) == True
        assert flow1.is_similar_to(flow3, spacing_tolerance=0.1) == False
        
        # Large tolerance
        assert flow1.is_similar_to(flow3, spacing_tolerance=0.6) == True
    
    def test_line_vertical_spacing_edge_cases(self):
        """Test line vertical spacing calculation edge cases."""
        # Lines at same position
        line1 = Line("Line 1", y_position=100.0, x_position=50.0, height=12.0)
        line2 = Line("Line 2", y_position=100.0, x_position=50.0, height=12.0)
        
        spacing = line1.vertical_spacing_to(line2)
        assert spacing == -12.0  # Overlap scenario
        
        # Lines with zero height
        line3 = Line("Line 3", y_position=100.0, x_position=50.0, height=0.0)
        line4 = Line("Line 4", y_position=90.0, x_position=50.0, height=0.0)
        
        spacing = line3.vertical_spacing_to(line4)
        assert spacing == 10.0  # Distance without height consideration
    
    def test_line_is_aligned_with_exact_match(self):
        """Test line alignment with exact position match."""
        line1 = Line("Line 1", y_position=100.0, x_position=50.0, height=12.0)
        line2 = Line("Line 2", y_position=85.0, x_position=50.0, height=12.0)
        
        assert line1.is_aligned_with(line2, tolerance=0.0) == True
    
    def test_line_is_aligned_with_boundary_tolerance(self):
        """Test line alignment at tolerance boundaries."""
        line1 = Line("Line 1", y_position=100.0, x_position=50.0, height=12.0)
        line2 = Line("Line 2", y_position=85.0, x_position=55.0, height=12.0)
        
        # Exactly at tolerance boundary
        assert line1.is_aligned_with(line2, tolerance=5.0) == True
        # Just outside tolerance
        assert line1.is_aligned_with(line2, tolerance=4.9) == False
    
    def test_paragraph_to_markdown_with_special_characters(self):
        """Test paragraph markdown output with special characters."""
        lines = [
            Line("Text with **bold** and *italic*", y_position=100.0, x_position=50.0, height=12.0),
            Line("Special chars: #heading & [link](url)", y_position=85.0, x_position=50.0, height=12.0)
        ]
        paragraph = Paragraph(lines=lines)
        
        markdown = paragraph.to_markdown()
        
        # Should preserve special characters as-is
        assert "**bold**" in markdown
        assert "*italic*" in markdown
        assert "#heading" in markdown
        assert "[link](url)" in markdown
    
    def test_document_markdown_with_mixed_content_types(self):
        """Test document markdown with various block types."""
        document = Document()
        
        # Add different block types
        document.add_block(Heading(level=1, content="Main Title"))
        document.add_block(TextBlock(content="Simple text block"))
        
        lines = [Line("Complex paragraph", y_position=100.0, x_position=50.0, height=12.0)]
        document.add_block(Paragraph(lines=lines))
        
        document.add_block(Heading(level=2, content="Subtitle"))
        
        markdown = document.to_markdown()
        
        # Verify all content is included with proper formatting
        assert "# Main Title" in markdown
        assert "Simple text block" in markdown
        assert "Complex paragraph" in markdown
        assert "## Subtitle" in markdown
        
        # Verify proper spacing
        lines = markdown.split('\n')
        # Should have empty lines after headings
        main_title_idx = next(i for i, line in enumerate(lines) if "# Main Title" in line)
        assert lines[main_title_idx + 1] == ""  # Empty line after main title