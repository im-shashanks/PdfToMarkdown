"""Integration tests for paragraph extraction functionality."""

import pytest

from pdf2markdown.domain.models.document import (
    Document, TextBlock, Heading, Paragraph
)
from pdf2markdown.domain.services.paragraph_detector import ParagraphDetector


class TestParagraphExtraction:
    """Integration tests for complete paragraph extraction workflow."""
    
    def test_end_to_end_paragraph_detection(self):
        """Test complete paragraph detection workflow."""
        # Create a document with mixed content
        document = Document(
            title="Test Document",
            blocks=[
                Heading(level=1, content="Introduction", font_size=14.0),
                TextBlock(
                    content="This is the first paragraph of the document. It contains multiple sentences that should be properly formatted.",
                    font_size=10.0
                ),
                TextBlock(
                    content="This is a second paragraph.\nIt spans multiple lines\nand should maintain proper structure.",
                    font_size=10.0
                ),
                Heading(level=2, content="Section Two", font_size=12.0),
                TextBlock(
                    content="A paragraph after a heading should be properly detected and formatted with appropriate spacing.",
                    font_size=10.0
                )
            ]
        )
        
        # Apply paragraph detection
        detector = ParagraphDetector()
        result = detector.detect_paragraphs_in_document(document)
        
        # Verify document structure
        assert len(result.blocks) == 5
        assert isinstance(result.blocks[0], Heading)  # Title remains
        assert isinstance(result.blocks[1], Paragraph)  # First TextBlock → Paragraph
        assert isinstance(result.blocks[2], Paragraph)  # Second TextBlock → Paragraph
        assert isinstance(result.blocks[3], Heading)  # Subtitle remains
        assert isinstance(result.blocks[4], Paragraph)  # Third TextBlock → Paragraph
        
        # Verify paragraph content
        first_paragraph = result.blocks[1]
        assert "first paragraph" in first_paragraph.content
        
        second_paragraph = result.blocks[2]
        assert len(second_paragraph.lines) == 3  # Multiple lines detected
        
        third_paragraph = result.blocks[4]
        assert "paragraph after a heading" in third_paragraph.content
    
    def test_paragraph_markdown_output(self):
        """Test that paragraphs produce correct markdown output."""
        document = Document(blocks=[
            TextBlock(content="Simple paragraph.", font_size=10.0),
            TextBlock(content="Another paragraph\nwith multiple lines.", font_size=10.0)
        ])
        
        detector = ParagraphDetector()
        result = detector.detect_paragraphs_in_document(document)
        
        # Convert to markdown
        markdown = result.to_markdown()
        
        # Verify markdown structure
        lines = markdown.split('\n')
        assert "Simple paragraph." in markdown
        assert "Another paragraph with multiple lines." in markdown
        
        # Verify proper spacing between paragraphs
        paragraph_lines = [line for line in lines if line.strip()]
        assert len(paragraph_lines) >= 2
    
    def test_complex_document_structure(self):
        """Test paragraph detection with complex document structure."""
        document = Document(
            title="Complex Document",
            blocks=[
                Heading(level=1, content="Main Title", font_size=16.0),
                TextBlock(content="Introduction paragraph with important information.", font_size=10.0),
                Heading(level=2, content="Methodology", font_size=14.0),
                TextBlock(content="First methodological paragraph.", font_size=10.0),
                TextBlock(content="Second methodological paragraph\nthat continues on next line\nand has multiple sentences.", font_size=10.0),
                Heading(level=2, content="Results", font_size=14.0),
                TextBlock(content="Results paragraph with findings.", font_size=10.0),
                Heading(level=1, content="Conclusion", font_size=16.0),
                TextBlock(content="Final concluding thoughts.", font_size=10.0)
            ]
        )
        
        detector = ParagraphDetector()
        result = detector.detect_paragraphs_in_document(document)
        
        # Count different block types
        headings = [b for b in result.blocks if isinstance(b, Heading)]
        paragraphs = [b for b in result.blocks if isinstance(b, Paragraph)]
        
        assert len(headings) == 4  # Original headings preserved
        assert len(paragraphs) == 5  # TextBlocks converted to paragraphs
        
        # Verify heading levels preserved
        heading_levels = [h.level for h in headings]
        assert heading_levels == [1, 2, 2, 1]
        
        # Verify paragraph content quality
        methodology_para = paragraphs[2]  # Third paragraph (second under Methodology) 
        assert len(methodology_para.lines) == 3  # Multi-line paragraph
        assert "methodological" in methodology_para.content
    
    def test_paragraph_continuation_detection(self):
        """Test detection and merging of paragraph continuations."""
        document = Document(blocks=[
            TextBlock(content="This is the start of a paragraph.", font_size=10.0),
            TextBlock(content="and this continues the thought", font_size=10.0),  # Continuation
            TextBlock(content="This starts a new paragraph entirely.", font_size=10.0)
        ])
        
        detector = ParagraphDetector()
        result = detector.detect_paragraphs_in_document(document)
        
        # Should have 2 paragraphs after merging continuation  
        paragraphs = [b for b in result.blocks if isinstance(b, Paragraph)]
        assert len(paragraphs) == 2
        
        # First paragraph should include continuation
        first_paragraph = paragraphs[0]
        assert "start of a paragraph" in first_paragraph.content
        assert "continues the thought" in first_paragraph.content
        
        # Second paragraph should be separate
        second_paragraph = paragraphs[1]
        assert "new paragraph entirely" in second_paragraph.content
    
    def test_indentation_preservation(self):
        """Test that meaningful indentation is preserved."""
        document = Document(blocks=[
            TextBlock(content="    This is an indented paragraph.", font_size=10.0),
            TextBlock(content="This is a normal paragraph.", font_size=10.0)
        ])
        
        detector = ParagraphDetector()
        result = detector.detect_paragraphs_in_document(document)
        
        markdown = result.to_markdown()
        
        # Check that indentation is preserved in output
        lines = markdown.split('\n')
        
        # Find the lines and check indentation
        has_indented = any(line.startswith("    ") and "indented paragraph" in line for line in lines)
        has_normal = any(not line.startswith("    ") and "normal paragraph" in line for line in lines)
        
        assert has_indented, f"Expected indented line not found in: {lines}"
        assert has_normal, f"Expected normal line not found in: {lines}"
    
    def test_empty_and_whitespace_handling(self):
        """Test handling of empty content and whitespace."""
        document = Document(blocks=[
            TextBlock(content="", font_size=10.0),  # Empty
            TextBlock(content="   \n\t  ", font_size=10.0),  # Whitespace only
            TextBlock(content="Valid content here.", font_size=10.0)
        ])
        
        detector = ParagraphDetector()
        result = detector.detect_paragraphs_in_document(document)
        
        # Should only have valid content paragraphs
        paragraphs = [b for b in result.blocks if isinstance(b, Paragraph)]
        non_empty_paragraphs = [p for p in paragraphs if not p.is_empty()]
        
        assert len(non_empty_paragraphs) == 1
        assert "Valid content here" in non_empty_paragraphs[0].content
    
    def test_performance_with_large_document(self):
        """Test performance with larger document structures."""
        # Create a document with many blocks
        blocks = []
        for i in range(50):
            if i % 10 == 0:
                blocks.append(Heading(level=2, content=f"Section {i//10 + 1}", font_size=12.0))
            else:
                blocks.append(TextBlock(
                    content=f"This is paragraph {i} with content that spans multiple words and sentences.",
                    font_size=10.0
                ))
        
        document = Document(title="Large Document", blocks=blocks)
        
        # Time the detection process
        import time
        start_time = time.time()
        
        detector = ParagraphDetector()
        result = detector.detect_paragraphs_in_document(document)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete quickly (under 1 second for 50 blocks)
        assert processing_time < 1.0
        
        # Verify all content processed
        assert len(result.blocks) == 50
        paragraphs = [b for b in result.blocks if isinstance(b, Paragraph)]
        headings = [b for b in result.blocks if isinstance(b, Heading)]
        
        assert len(paragraphs) >= 40  # Most TextBlocks should become paragraphs
        assert len(headings) == 5