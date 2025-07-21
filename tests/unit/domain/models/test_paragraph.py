"""Unit tests for paragraph domain models."""

import pytest
from dataclasses import FrozenInstanceError

from pdf2markdown.domain.models.document import Paragraph, Line, TextFlow, TextAlignment


class TestLine:
    """Test cases for Line value object."""

    def test_line_creation(self):
        """Test creating a Line with valid data."""
        line = Line(
            text="This is a line of text",
            y_position=100.0,
            x_position=50.0,
            height=12.0,
            font_size=10.0
        )
        
        assert line.text == "This is a line of text"
        assert line.y_position == 100.0
        assert line.x_position == 50.0
        assert line.height == 12.0
        assert line.font_size == 10.0

    def test_line_immutability(self):
        """Test that Line is immutable."""
        line = Line(
            text="Immutable text",
            y_position=100.0,
            x_position=50.0,
            height=12.0
        )
        
        with pytest.raises(FrozenInstanceError):
            line.text = "Modified text"

    def test_line_defaults(self):
        """Test Line default values."""
        line = Line(
            text="Text",
            y_position=100.0,
            x_position=50.0,
            height=12.0
        )
        
        assert line.font_size is None

    def test_line_spacing_calculation(self):
        """Test vertical spacing calculation between lines."""
        line1 = Line("Line 1", y_position=100.0, x_position=50.0, height=12.0)
        line2 = Line("Line 2", y_position=85.0, x_position=50.0, height=12.0)
        
        spacing = line1.vertical_spacing_to(line2)
        assert spacing == 3.0  # 100 - 85 - 12 = 3

    def test_line_is_aligned_with(self):
        """Test horizontal alignment detection."""
        line1 = Line("Line 1", y_position=100.0, x_position=50.0, height=12.0)
        line2 = Line("Line 2", y_position=85.0, x_position=52.0, height=12.0)
        line3 = Line("Line 3", y_position=70.0, x_position=100.0, height=12.0)
        
        assert line1.is_aligned_with(line2, tolerance=5.0) is True
        assert line1.is_aligned_with(line3, tolerance=5.0) is False


class TestTextFlow:
    """Test cases for TextFlow value object."""

    def test_text_flow_creation(self):
        """Test creating TextFlow with valid data."""
        flow = TextFlow(
            alignment=TextAlignment.LEFT,
            line_spacing=1.5,
            indentation=20.0,
            average_line_height=12.0
        )
        
        assert flow.alignment == TextAlignment.LEFT
        assert flow.line_spacing == 1.5
        assert flow.indentation == 20.0
        assert flow.average_line_height == 12.0

    def test_text_flow_immutability(self):
        """Test that TextFlow is immutable."""
        flow = TextFlow(
            alignment=TextAlignment.CENTER,
            line_spacing=1.0
        )
        
        with pytest.raises(FrozenInstanceError):
            flow.alignment = TextAlignment.RIGHT

    def test_text_flow_defaults(self):
        """Test TextFlow default values."""
        flow = TextFlow()
        
        assert flow.alignment == TextAlignment.LEFT
        assert flow.line_spacing == 1.0
        assert flow.indentation == 0.0
        assert flow.average_line_height == 12.0

    def test_text_flow_is_similar_to(self):
        """Test similarity comparison between TextFlows."""
        flow1 = TextFlow(alignment=TextAlignment.LEFT, line_spacing=1.5)
        flow2 = TextFlow(alignment=TextAlignment.LEFT, line_spacing=1.4)
        flow3 = TextFlow(alignment=TextAlignment.CENTER, line_spacing=1.5)
        
        assert flow1.is_similar_to(flow2, spacing_tolerance=0.2) is True
        assert flow1.is_similar_to(flow3, spacing_tolerance=0.2) is False


class TestParagraph:
    """Test cases for Paragraph entity."""

    def test_paragraph_creation(self):
        """Test creating a Paragraph with valid data."""
        lines = [
            Line("First line", y_position=100.0, x_position=50.0, height=12.0),
            Line("Second line", y_position=85.0, x_position=50.0, height=12.0)
        ]
        flow = TextFlow(alignment=TextAlignment.JUSTIFY, line_spacing=1.5)
        
        paragraph = Paragraph(
            lines=lines,
            text_flow=flow,
            font_size=10.0,
            is_continuation=False
        )
        
        assert len(paragraph.lines) == 2
        assert paragraph.text_flow == flow
        assert paragraph.font_size == 10.0
        assert paragraph.is_continuation is False

    def test_paragraph_content_property(self):
        """Test content property concatenates lines."""
        lines = [
            Line("First line", y_position=100.0, x_position=50.0, height=12.0),
            Line("Second line", y_position=85.0, x_position=50.0, height=12.0),
            Line("Third line", y_position=70.0, x_position=50.0, height=12.0)
        ]
        
        paragraph = Paragraph(lines=lines)
        assert paragraph.content == "First line Second line Third line"

    def test_paragraph_empty_lines(self):
        """Test paragraph with empty lines."""
        paragraph = Paragraph(lines=[])
        assert paragraph.content == ""
        assert len(paragraph.lines) == 0

    def test_paragraph_to_markdown_basic(self):
        """Test basic markdown conversion."""
        lines = [
            Line("This is a paragraph.", y_position=100.0, x_position=50.0, height=12.0)
        ]
        paragraph = Paragraph(lines=lines)
        
        markdown = paragraph.to_markdown()
        assert markdown == "This is a paragraph.\n"

    def test_paragraph_to_markdown_multiline(self):
        """Test markdown conversion with multiple lines."""
        lines = [
            Line("First line of text", y_position=100.0, x_position=50.0, height=12.0),
            Line("continues on second line", y_position=85.0, x_position=50.0, height=12.0),
            Line("and ends here.", y_position=70.0, x_position=50.0, height=12.0)
        ]
        paragraph = Paragraph(lines=lines)
        
        markdown = paragraph.to_markdown()
        assert markdown == "First line of text continues on second line and ends here.\n"

    def test_paragraph_to_markdown_with_indentation(self):
        """Test markdown conversion preserves meaningful indentation."""
        lines = [
            Line("    Indented paragraph", y_position=100.0, x_position=70.0, height=12.0),
            Line("    continues here", y_position=85.0, x_position=70.0, height=12.0)
        ]
        flow = TextFlow(indentation=20.0)
        paragraph = Paragraph(lines=lines, text_flow=flow)
        
        markdown = paragraph.to_markdown()
        assert markdown == "    Indented paragraph     continues here\n"

    def test_paragraph_to_markdown_hard_line_breaks(self):
        """Test markdown with hard line breaks."""
        lines = [
            Line("Line one", y_position=100.0, x_position=50.0, height=12.0),
            Line("Line two", y_position=75.0, x_position=50.0, height=12.0),  # Large gap
            Line("Line three", y_position=60.0, x_position=50.0, height=12.0)
        ]
        paragraph = Paragraph(lines=lines, preserve_line_breaks=True)
        
        markdown = paragraph.to_markdown()
        assert markdown == "Line one  \nLine two  \nLine three\n"

    def test_paragraph_add_line(self):
        """Test adding a line to paragraph."""
        paragraph = Paragraph(lines=[])
        line = Line("New line", y_position=100.0, x_position=50.0, height=12.0)
        
        paragraph.add_line(line)
        assert len(paragraph.lines) == 1
        assert paragraph.lines[0] == line

    def test_paragraph_merge_with(self):
        """Test merging two paragraphs."""
        lines1 = [Line("Para 1", y_position=100.0, x_position=50.0, height=12.0)]
        lines2 = [Line("Para 2", y_position=85.0, x_position=50.0, height=12.0)]
        
        para1 = Paragraph(lines=lines1)
        para2 = Paragraph(lines=lines2)
        
        para1.merge_with(para2)
        assert len(para1.lines) == 2
        assert para1.content == "Para 1 Para 2"

    def test_paragraph_bounding_box(self):
        """Test calculating paragraph bounding box."""
        lines = [
            Line("Top line", y_position=100.0, x_position=50.0, height=12.0),
            Line("Middle", y_position=85.0, x_position=60.0, height=12.0),
            Line("Bottom", y_position=70.0, x_position=55.0, height=12.0)
        ]
        paragraph = Paragraph(lines=lines)
        
        bbox = paragraph.get_bounding_box()
        assert bbox["top"] == 100.0
        assert bbox["bottom"] == 70.0
        assert bbox["left"] == 50.0
        assert bbox["right"] == 60.0  # Assumes text extends somewhat from x_position

    def test_paragraph_is_empty(self):
        """Test empty paragraph detection."""
        empty_para = Paragraph(lines=[])
        whitespace_para = Paragraph(lines=[
            Line("   ", y_position=100.0, x_position=50.0, height=12.0),
            Line("\t", y_position=85.0, x_position=50.0, height=12.0)
        ])
        content_para = Paragraph(lines=[
            Line("Content", y_position=100.0, x_position=50.0, height=12.0)
        ])
        
        assert empty_para.is_empty() is True
        assert whitespace_para.is_empty() is True
        assert content_para.is_empty() is False