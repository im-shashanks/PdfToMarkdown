"""Unit tests for paragraph detection service."""

import pytest
from unittest.mock import Mock

from pdf2markdown.domain.models.document import (
    Document, TextBlock, Paragraph, Line, TextFlow, TextAlignment
)
from pdf2markdown.domain.services.paragraph_detector import ParagraphDetector


class TestParagraphDetector:
    """Test cases for ParagraphDetector service."""
    
    def test_init_with_default_config(self):
        """Test ParagraphDetector initialization with default configuration."""
        detector = ParagraphDetector()
        
        assert detector.line_spacing_threshold == 1.8
        assert detector.min_paragraph_lines == 1
        assert detector.indentation_threshold == 10.0
        assert detector.alignment_tolerance == 5.0
    
    def test_init_with_custom_config(self):
        """Test ParagraphDetector initialization with custom configuration."""
        detector = ParagraphDetector(
            line_spacing_threshold=2.0,
            min_paragraph_lines=2,
            indentation_threshold=15.0,
            alignment_tolerance=3.0
        )
        
        assert detector.line_spacing_threshold == 2.0
        assert detector.min_paragraph_lines == 2
        assert detector.indentation_threshold == 15.0
        assert detector.alignment_tolerance == 3.0
    
    def test_detect_paragraphs_in_empty_document(self):
        """Test paragraph detection in an empty document."""
        detector = ParagraphDetector()
        empty_document = Document(title="Empty", blocks=[])
        
        result = detector.detect_paragraphs_in_document(empty_document)
        
        assert len(result.blocks) == 0
        assert result.title == "Empty"
    
    def test_detect_paragraphs_in_document_preserves_headings(self):
        """Test that paragraph detection preserves existing headings."""
        from pdf2markdown.domain.models.document import Heading
        
        detector = ParagraphDetector()
        document = Document(blocks=[
            Heading(level=1, content="Title", font_size=14.0),
            TextBlock(content="Sample text", font_size=10.0),
            Heading(level=2, content="Subtitle", font_size=12.0)
        ])
        
        result = detector.detect_paragraphs_in_document(document)
        
        assert len(result.blocks) == 3
        assert isinstance(result.blocks[0], Heading)
        assert isinstance(result.blocks[1], Paragraph)
        assert isinstance(result.blocks[2], Heading)
    
    def test_convert_simple_text_block_to_paragraph(self):
        """Test converting a simple TextBlock to Paragraph."""
        detector = ParagraphDetector()
        text_block = TextBlock(content="This is a simple paragraph.", font_size=10.0)
        
        paragraph = detector.convert_text_block_to_paragraph(text_block)
        
        assert isinstance(paragraph, Paragraph)
        assert len(paragraph.lines) == 1
        assert paragraph.lines[0].text == "This is a simple paragraph."
        assert paragraph.font_size == 10.0
    
    def test_convert_multiline_text_block_to_paragraph(self):
        """Test converting multiline TextBlock to Paragraph with line detection."""
        detector = ParagraphDetector()
        multiline_text = "Line one of text.\nLine two continues here.\nFinal line ends here."
        text_block = TextBlock(content=multiline_text, font_size=10.0)
        
        paragraph = detector.convert_text_block_to_paragraph(text_block)
        
        assert len(paragraph.lines) == 3
        assert paragraph.lines[0].text == "Line one of text."
        assert paragraph.lines[1].text == "Line two continues here."
        assert paragraph.lines[2].text == "Final line ends here."
    
    def test_analyze_line_spacing_normal(self):
        """Test line spacing analysis for normal paragraph spacing."""
        detector = ParagraphDetector()
        lines = [
            Line("Line 1", y_position=100.0, x_position=50.0, height=12.0),
            Line("Line 2", y_position=85.0, x_position=50.0, height=12.0),
            Line("Line 3", y_position=70.0, x_position=50.0, height=12.0)
        ]
        
        spacing_analysis = detector._analyze_line_spacing(lines)
        
        assert spacing_analysis["average_spacing"] == 3.0  # 15 - 12 = 3
        assert spacing_analysis["spacing_consistency"] > 0.8  # High consistency
    
    def test_analyze_line_spacing_paragraph_break(self):
        """Test line spacing analysis detecting paragraph breaks."""
        detector = ParagraphDetector()
        lines = [
            Line("Para 1 Line 1", y_position=100.0, x_position=50.0, height=12.0),
            Line("Para 1 Line 2", y_position=85.0, x_position=50.0, height=12.0),
            # Large gap indicating paragraph break
            Line("Para 2 Line 1", y_position=60.0, x_position=50.0, height=12.0),
            Line("Para 2 Line 2", y_position=45.0, x_position=50.0, height=12.0)
        ]
        
        spacing_analysis = detector._analyze_line_spacing(lines)
        
        # Should detect the large gap
        assert len(spacing_analysis["paragraph_breaks"]) == 1
        assert spacing_analysis["paragraph_breaks"][0] == 2  # Index of paragraph break
    
    def test_detect_text_alignment_left(self):
        """Test detecting left alignment in text lines."""
        detector = ParagraphDetector()
        lines = [
            Line("Left aligned text", y_position=100.0, x_position=50.0, height=12.0),
            Line("More left text", y_position=85.0, x_position=52.0, height=12.0),
            Line("Still left", y_position=70.0, x_position=48.0, height=12.0)
        ]
        
        alignment = detector._detect_text_alignment(lines)
        
        assert alignment == TextAlignment.LEFT
    
    def test_detect_text_alignment_center(self):
        """Test detecting center alignment in text lines."""
        detector = ParagraphDetector()
        lines = [
            Line("Centered", y_position=100.0, x_position=150.0, height=12.0),
            Line("Text", y_position=85.0, x_position=170.0, height=12.0),
            Line("Lines", y_position=70.0, x_position=160.0, height=12.0)
        ]
        
        alignment = detector._detect_text_alignment(lines)
        
        assert alignment == TextAlignment.CENTER
    
    def test_detect_indentation_none(self):
        """Test detecting no indentation."""
        detector = ParagraphDetector()
        lines = [
            Line("No indent", y_position=100.0, x_position=50.0, height=12.0),
            Line("Still none", y_position=85.0, x_position=52.0, height=12.0)
        ]
        
        indentation = detector._detect_indentation(lines)
        
        assert indentation < detector.indentation_threshold
    
    def test_detect_indentation_present(self):
        """Test detecting meaningful indentation."""
        detector = ParagraphDetector()
        lines = [
            Line("    Indented text", y_position=100.0, x_position=70.0, height=12.0),
            Line("    More indented", y_position=85.0, x_position=72.0, height=12.0)
        ]
        
        indentation = detector._detect_indentation(lines)
        
        assert indentation >= detector.indentation_threshold
    
    def test_merge_continuous_paragraphs_no_merge(self):
        """Test that non-continuous paragraphs are not merged."""
        detector = ParagraphDetector()
        para1 = Paragraph(lines=[
            Line("First paragraph", y_position=100.0, x_position=50.0, height=12.0)
        ])
        para2 = Paragraph(lines=[
            Line("Second paragraph", y_position=70.0, x_position=50.0, height=12.0)
        ])
        
        result = detector.merge_continuous_paragraphs([para1, para2])
        
        assert len(result) == 2
        assert result[0] is para1
        assert result[1] is para2
    
    def test_merge_continuous_paragraphs_with_merge(self):
        """Test that continuous paragraphs are merged correctly."""
        detector = ParagraphDetector()
        # Paragraphs with similar text flow should be merged
        flow = TextFlow(alignment=TextAlignment.LEFT, line_spacing=1.0)
        para1 = Paragraph(
            lines=[Line("First part", y_position=100.0, x_position=50.0, height=12.0)],
            text_flow=flow
        )
        para2 = Paragraph(
            lines=[Line("continues here", y_position=85.0, x_position=50.0, height=12.0)],
            text_flow=flow,
            is_continuation=True
        )
        
        result = detector.merge_continuous_paragraphs([para1, para2])
        
        assert len(result) == 1
        assert len(result[0].lines) == 2
        assert result[0].content == "First part continues here"
    
    def test_create_text_flow_from_lines(self):
        """Test creating TextFlow from line analysis."""
        detector = ParagraphDetector()
        lines = [
            Line("Regular text", y_position=100.0, x_position=50.0, height=12.0),
            Line("More text", y_position=85.0, x_position=52.0, height=12.0)
        ]
        
        text_flow = detector._create_text_flow_from_lines(lines)
        
        assert isinstance(text_flow, TextFlow)
        assert text_flow.alignment == TextAlignment.LEFT
        assert text_flow.line_spacing > 0.0
        assert text_flow.average_line_height == 12.0
    
    def test_is_paragraph_continuation(self):
        """Test detecting if a paragraph is a continuation of previous text."""
        detector = ParagraphDetector()
        
        # Normal paragraph starting
        lines_normal = [
            Line("This starts a new paragraph.", y_position=100.0, x_position=50.0, height=12.0)
        ]
        
        # Continuation paragraph (starts with lowercase, no punctuation ending previous)
        lines_continuation = [
            Line("continues from previous line", y_position=85.0, x_position=50.0, height=12.0)
        ]
        
        normal_para = Paragraph(lines=lines_normal)
        continuation_para = Paragraph(lines=lines_continuation)
        
        assert detector._is_paragraph_continuation(normal_para) is False
        assert detector._is_paragraph_continuation(continuation_para) is True
    
    def test_split_lines_at_paragraph_breaks(self):
        """Test splitting lines into separate paragraphs at detected breaks."""
        detector = ParagraphDetector()
        lines = [
            Line("Para 1 line 1", y_position=100.0, x_position=50.0, height=12.0),
            Line("Para 1 line 2", y_position=85.0, x_position=50.0, height=12.0),
            Line("Para 2 line 1", y_position=60.0, x_position=50.0, height=12.0),  # Big gap
            Line("Para 2 line 2", y_position=45.0, x_position=50.0, height=12.0)
        ]
        break_indices = [2]  # Break at index 2
        
        paragraphs = detector._split_lines_at_paragraph_breaks(lines, break_indices)
        
        assert len(paragraphs) == 2
        assert len(paragraphs[0].lines) == 2
        assert len(paragraphs[1].lines) == 2
        assert paragraphs[0].content == "Para 1 line 1 Para 1 line 2"
        assert paragraphs[1].content == "Para 2 line 1 Para 2 line 2"