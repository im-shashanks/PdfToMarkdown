"""Unit tests for markdown formatter."""

import tempfile
from pathlib import Path

import pytest

from pdf2markdown.domain.models import Document, Heading, TextBlock
from pdf2markdown.infrastructure.formatters import MarkdownFormatter


class TestMarkdownFormatter:
    """Test suite for MarkdownFormatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = MarkdownFormatter()
    
    def test_formatter_initialization(self):
        """Test formatter initializes correctly."""
        # Arrange & Act
        formatter = MarkdownFormatter()
        
        # Assert
        assert formatter.logger is not None
        assert formatter.logger.name == "pdf2markdown.infrastructure.formatters.markdown_formatter"
    
    def test_format_document_empty(self):
        """Test formatting empty document."""
        # Arrange
        document = Document()
        
        # Act
        result = self.formatter.format_document(document)
        
        # Assert
        assert result == ""
    
    def test_format_document_none(self):
        """Test formatting None document."""
        # Arrange
        document = None
        
        # Act
        result = self.formatter.format_document(document)
        
        # Assert
        assert result == ""
    
    def test_format_document_with_title_only(self):
        """Test formatting document with only title."""
        # Arrange
        document = Document(title="Test Document")
        
        # Act
        result = self.formatter.format_document(document)
        
        # Assert
        assert result == "# Test Document"
    
    def test_format_document_with_headings_and_text(self):
        """Test formatting document with headings and text blocks."""
        # Arrange
        document = Document(title="Main Document")
        document.add_block(Heading(level=2, content="Introduction"))
        document.add_block(TextBlock(content="This is the introduction paragraph."))
        document.add_block(Heading(level=3, content="Details"))
        document.add_block(TextBlock(content="Here are the details."))
        
        # Act
        result = self.formatter.format_document(document)
        
        # Assert
        expected = """# Main Document

## Introduction

This is the introduction paragraph.
### Details

Here are the details."""
        assert result == expected
    
    def test_format_document_complex(self):
        """Test formatting complex document with multiple elements."""
        # Arrange
        document = Document()
        document.add_block(Heading(level=1, content="Chapter 1"))
        document.add_block(TextBlock(content="First paragraph content."))
        document.add_block(Heading(level=2, content="Section A"))
        document.add_block(TextBlock(content="Section A content."))
        document.add_block(Heading(level=2, content="Section B"))
        document.add_block(TextBlock(content="Section B content."))
        document.add_block(Heading(level=3, content="Subsection"))
        document.add_block(TextBlock(content="Subsection content."))
        
        # Act
        result = self.formatter.format_document(document)
        
        # Assert
        expected = """# Chapter 1

First paragraph content.
## Section A

Section A content.
## Section B

Section B content.
### Subsection

Subsection content."""
        assert result == expected
    
    def test_format_to_file_success(self):
        """Test successful file output."""
        # Arrange
        document = Document(title="Test Document")
        document.add_block(Heading(level=2, content="Heading"))
        document.add_block(TextBlock(content="Content here."))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Act
            self.formatter.format_to_file(document, temp_path)
            
            # Assert
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            expected = """# Test Document

## Heading

Content here."""
            assert content == expected
            
        finally:
            Path(temp_path).unlink()
    
    def test_format_to_file_invalid_path(self):
        """Test file output with invalid path raises IOError."""
        # Arrange
        document = Document(title="Test")
        invalid_path = "/invalid/directory/file.md"
        
        # Act & Assert
        with pytest.raises(IOError, match="Failed to write markdown file"):
            self.formatter.format_to_file(document, invalid_path)
    
    def test_format_document_with_metadata(self):
        """Test that formatting works with document metadata."""
        # Arrange
        document = Document(
            title="Document with Metadata",
            metadata={
                "author": "Test Author",
                "date": "2025-01-19",
                "version": "1.0"
            }
        )
        document.add_block(TextBlock(content="Document content."))
        
        # Act
        result = self.formatter.format_document(document)
        
        # Assert
        # Metadata is not included in markdown output by default
        expected = """# Document with Metadata

Document content."""
        assert result == expected
    
    def test_format_document_preserves_heading_hierarchy(self):
        """Test that heading hierarchy is preserved in output."""
        # Arrange
        document = Document()
        document.add_block(Heading(level=1, content="H1 Title"))
        document.add_block(Heading(level=2, content="H2 Subtitle"))
        document.add_block(Heading(level=3, content="H3 Section"))
        document.add_block(Heading(level=4, content="H4 Subsection"))
        document.add_block(Heading(level=5, content="H5 Minor"))
        document.add_block(Heading(level=6, content="H6 Tiny"))
        
        # Act
        result = self.formatter.format_document(document)
        
        # Assert
        expected = """# H1 Title

## H2 Subtitle

### H3 Section

#### H4 Subsection

##### H5 Minor

###### H6 Tiny"""
        assert result == expected