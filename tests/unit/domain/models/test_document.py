"""Unit tests for document domain models following TDD principles."""

import pytest

from pdf2markdown.domain.models import Block, Document, Heading, TextBlock


class TestHeading:
    """Test suite for Heading model."""
    
    def test_heading_creation_valid(self):
        """Test creating a valid heading."""
        # Arrange
        level = 2
        content = "Chapter 1: Introduction"
        font_size = 18.0
        
        # Act
        heading = Heading(level=level, content=content, font_size=font_size, is_bold=True)
        
        # Assert
        assert heading.level == level
        assert heading.content == content
        assert heading.font_size == font_size
        assert heading.is_bold is True
    
    def test_heading_level_validation(self):
        """Test heading level must be between 1 and 6."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
            Heading(level=0, content="Invalid")
        
        with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
            Heading(level=7, content="Invalid")
    
    def test_heading_content_validation(self):
        """Test heading content cannot be empty."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Heading content cannot be empty"):
            Heading(level=1, content="")
        
        with pytest.raises(ValueError, match="Heading content cannot be empty"):
            Heading(level=1, content="   ")
    
    def test_heading_to_markdown(self):
        """Test converting heading to markdown format."""
        # Arrange
        test_cases = [
            (1, "Main Title", "# Main Title"),
            (2, "  Subtitle  ", "## Subtitle"),
            (3, "Section 3", "### Section 3"),
            (4, "Subsection", "#### Subsection"),
            (5, "Minor Heading", "##### Minor Heading"),
            (6, "Tiny Heading", "###### Tiny Heading"),
        ]
        
        # Act & Assert
        for level, content, expected in test_cases:
            heading = Heading(level=level, content=content)
            assert heading.to_markdown() == expected


class TestTextBlock:
    """Test suite for TextBlock model."""
    
    def test_text_block_creation(self):
        """Test creating a text block."""
        # Arrange
        content = "This is a paragraph of text."
        font_size = 12.0
        
        # Act
        text_block = TextBlock(content=content, font_size=font_size)
        
        # Assert
        assert text_block.content == content
        assert text_block.font_size == font_size
    
    def test_text_block_to_markdown(self):
        """Test converting text block to markdown."""
        # Arrange
        content = "  This is a paragraph with spaces.  "
        text_block = TextBlock(content=content)
        
        # Act
        result = text_block.to_markdown()
        
        # Assert
        assert result == "This is a paragraph with spaces."
    
    def test_text_block_empty_content(self):
        """Test text block with empty content."""
        # Arrange
        text_block = TextBlock(content="")
        
        # Act
        result = text_block.to_markdown()
        
        # Assert
        assert result == ""


class TestDocument:
    """Test suite for Document model."""
    
    def test_document_creation(self):
        """Test creating an empty document."""
        # Arrange & Act
        doc = Document()
        
        # Assert
        assert doc.title is None
        assert doc.blocks == []
        assert doc.metadata == {}
    
    def test_document_with_title(self):
        """Test creating document with title."""
        # Arrange
        title = "Project Report"
        metadata = {"author": "John Doe", "date": "2025-01-19"}
        
        # Act
        doc = Document(title=title, metadata=metadata)
        
        # Assert
        assert doc.title == title
        assert doc.metadata == metadata
    
    def test_add_block_valid(self):
        """Test adding valid blocks to document."""
        # Arrange
        doc = Document()
        heading = Heading(level=1, content="Title")
        text = TextBlock(content="Content")
        
        # Act
        doc.add_block(heading)
        doc.add_block(text)
        
        # Assert
        assert len(doc.blocks) == 2
        assert doc.blocks[0] == heading
        assert doc.blocks[1] == text
    
    def test_add_block_invalid_type(self):
        """Test adding invalid type raises TypeError."""
        # Arrange
        doc = Document()
        invalid_block = "Not a Block instance"
        
        # Act & Assert
        with pytest.raises(TypeError, match="Expected Block instance"):
            doc.add_block(invalid_block)
    
    def test_document_to_markdown_empty(self):
        """Test converting empty document to markdown."""
        # Arrange
        doc = Document()
        
        # Act
        result = doc.to_markdown()
        
        # Assert
        assert result == ""
    
    def test_document_to_markdown_with_title(self):
        """Test converting document with title to markdown."""
        # Arrange
        doc = Document(title="My Document")
        
        # Act
        result = doc.to_markdown()
        
        # Assert
        assert result == "# My Document"
    
    def test_document_to_markdown_complete(self):
        """Test converting complete document to markdown."""
        # Arrange
        doc = Document(title="Report")
        doc.add_block(Heading(level=2, content="Introduction"))
        doc.add_block(TextBlock(content="This is the introduction paragraph."))
        doc.add_block(Heading(level=2, content="Content"))
        doc.add_block(TextBlock(content="This is the main content."))
        doc.add_block(Heading(level=3, content="Subsection"))
        doc.add_block(TextBlock(content="Details here."))
        
        # Act
        result = doc.to_markdown()
        
        # Assert
        expected = """# Report

## Introduction

This is the introduction paragraph.
## Content

This is the main content.
### Subsection

Details here."""
        assert result == expected
    
    def test_block_abstract_methods(self):
        """Test that Block is abstract and cannot be instantiated."""
        # Arrange & Act & Assert
        with pytest.raises(TypeError):
            Block()  # Cannot instantiate abstract class