"""Unit tests for heading detection service."""

import pytest

from pdf2markdown.domain.interfaces import TextElement
from pdf2markdown.domain.models import Document, Heading, TextBlock
from pdf2markdown.domain.services import HeadingDetector, HeadingDetectionConfig


class TestHeadingDetectionConfig:
    """Test suite for HeadingDetectionConfig."""
    
    def test_default_config_creation(self):
        """Test creating config with default values."""
        # Arrange & Act
        config = HeadingDetectionConfig()
        
        # Assert
        assert config.level_multipliers[1] == 1.8  # H1 (updated value)
        assert config.level_multipliers[6] == 1.02  # H6 (updated value)
        assert config.min_size_difference == 0.1  # Updated value
        assert config.bold_weight == 0.1
        assert config.italic_weight == 0.05
        assert config.min_heading_length == 1
        assert config.max_heading_length == 200
    
    def test_custom_config_creation(self):
        """Test creating config with custom values."""
        # Arrange
        custom_multipliers = {1: 2.5, 2: 2.0, 3: 1.8, 4: 1.5, 5: 1.3, 6: 1.2}
        
        # Act
        config = HeadingDetectionConfig(
            level_multipliers=custom_multipliers,
            min_size_difference=2.0,
            bold_weight=0.2,
            max_heading_length=100
        )
        
        # Assert
        assert config.level_multipliers == custom_multipliers
        assert config.min_size_difference == 2.0
        assert config.bold_weight == 0.2
        assert config.max_heading_length == 100


class TestHeadingDetector:
    """Test suite for HeadingDetector service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = HeadingDetector()
        self.custom_config = HeadingDetectionConfig(
            level_multipliers={1: 2.0, 2: 1.5, 3: 1.3, 4: 1.2, 5: 1.1, 6: 1.05},
            min_size_difference=1.0
        )
    
    def test_detector_initialization_default(self):
        """Test detector initializes with default config."""
        # Arrange & Act
        detector = HeadingDetector()
        
        # Assert
        assert detector.config is not None
        assert isinstance(detector.config, HeadingDetectionConfig)
        assert detector.logger is not None
    
    def test_detector_initialization_custom_config(self):
        """Test detector initializes with custom config."""
        # Arrange & Act
        detector = HeadingDetector(self.custom_config)
        
        # Assert
        assert detector.config == self.custom_config
    
    def test_calculate_baseline_font_size_mode(self):
        """Test baseline calculation using statistical mode."""
        # Arrange
        text_elements = [
            TextElement(content="Text 1", font_size=12.0),
            TextElement(content="Text 2", font_size=12.0),
            TextElement(content="Text 3", font_size=12.0),
            TextElement(content="Heading", font_size=18.0),
        ]
        
        # Act
        baseline = self.detector._calculate_baseline_font_size(text_elements)
        
        # Assert
        assert baseline == 12.0
    
    def test_calculate_baseline_font_size_min_fallback(self):
        """Test baseline calculation fallback to min when no mode."""
        # Arrange
        text_elements = [
            TextElement(content="Text 1", font_size=10.0),
            TextElement(content="Text 2", font_size=12.0),
            TextElement(content="Text 3", font_size=14.0),
            TextElement(content="Text 4", font_size=16.0),
        ]
        
        # Act
        baseline = self.detector._calculate_baseline_font_size(text_elements)
        
        # Assert
        assert baseline == 10.0  # Min of [10, 12, 14, 16]
    
    def test_calculate_baseline_font_size_empty_list(self):
        """Test baseline calculation with empty list returns default."""
        # Arrange
        text_elements = []
        
        # Act
        baseline = self.detector._calculate_baseline_font_size(text_elements)
        
        # Assert
        assert baseline == 12.0  # Default
    
    def test_determine_heading_level_h1(self):
        """Test H1 heading detection."""
        # Arrange
        text_block = TextBlock(content="Main Title", font_size=24.0)
        baseline = 12.0
        
        # Act
        level = self.detector._determine_heading_level(text_block, baseline)
        
        # Assert
        assert level == 1  # 24/12 = 2.0 ratio >= H1 threshold (2.0)
    
    def test_determine_heading_level_h2(self):
        """Test H2 heading detection with content-aware logic."""
        # Arrange
        text_block = TextBlock(content="EXPERIENCE", font_size=21.6)  # Major section keyword
        baseline = 12.0
        
        # Act
        level = self.detector._determine_heading_level(text_block, baseline)
        
        # Assert
        assert level == 2  # Major section keywords are H2 level
    
    def test_determine_heading_level_not_heading(self):
        """Test text that should not be detected as heading."""
        # Arrange
        text_block = TextBlock(content="Regular paragraph text", font_size=12.5)
        baseline = 12.0
        
        # Act
        level = self.detector._determine_heading_level(text_block, baseline)
        
        # Assert  
        # Regular paragraph text should not be detected as heading despite font size difference
        assert level is None  # Enhanced algorithm correctly rejects generic text as heading
    
    def test_determine_heading_level_content_too_long(self):
        """Test that very long content is not detected as heading."""
        # Arrange
        long_content = "This is a very long text that should not be considered a heading " * 10
        text_block = TextBlock(content=long_content, font_size=24.0)
        baseline = 12.0
        
        # Act
        level = self.detector._determine_heading_level(text_block, baseline)
        
        # Assert
        assert level is None  # Content too long for heading
    
    def test_determine_heading_level_content_too_short(self):
        """Test that very short content is not detected as heading."""
        # Arrange
        text_block = TextBlock(content="", font_size=24.0)
        baseline = 12.0
        
        # Act
        level = self.detector._determine_heading_level(text_block, baseline)
        
        # Assert
        assert level is None  # Content too short
    
    def test_determine_heading_level_no_font_size(self):
        """Test that text without font size is not detected as heading."""
        # Arrange
        text_block = TextBlock(content="Some text", font_size=None)
        baseline = 12.0
        
        # Act
        level = self.detector._determine_heading_level(text_block, baseline)
        
        # Assert
        assert level is None
    
    def test_detect_headings_in_document_simple(self):
        """Test heading detection in a simple document."""
        # Arrange
        document = Document()
        document.add_block(TextBlock(content="Main Title", font_size=24.0))  # H1: 24/12=2.0
        document.add_block(TextBlock(content="Regular paragraph text here.", font_size=12.0))
        document.add_block(TextBlock(content="EXPERIENCE", font_size=21.6))  # H2: Major section
        document.add_block(TextBlock(content="More paragraph content.", font_size=12.0))
        
        # Act
        result_doc = self.detector.detect_headings_in_document(document)
        
        # Assert
        assert len(result_doc.blocks) == 4
        
        # First block should be H1
        assert isinstance(result_doc.blocks[0], Heading)
        assert result_doc.blocks[0].level == 1
        assert result_doc.blocks[0].content == "Main Title"
        
        # Second block should remain text
        assert isinstance(result_doc.blocks[1], TextBlock)
        assert result_doc.blocks[1].content == "Regular paragraph text here."
        
        # Third block should be H2
        assert isinstance(result_doc.blocks[2], Heading)
        assert result_doc.blocks[2].level == 2
        assert result_doc.blocks[2].content == "EXPERIENCE"
        
        # Fourth block should remain text
        assert isinstance(result_doc.blocks[3], TextBlock)
        assert result_doc.blocks[3].content == "More paragraph content."
    
    def test_detect_headings_in_document_empty(self):
        """Test heading detection in empty document."""
        # Arrange
        document = Document()
        
        # Act
        result_doc = self.detector.detect_headings_in_document(document)
        
        # Assert
        assert len(result_doc.blocks) == 0
        assert result_doc.title == document.title
        assert result_doc.metadata == document.metadata
    
    def test_detect_headings_preserves_metadata(self):
        """Test that heading detection preserves document metadata."""
        # Arrange
        document = Document(
            title="Test Document",
            metadata={"author": "Test Author", "date": "2025-01-19"}
        )
        document.add_block(TextBlock(content="Content", font_size=12.0))
        
        # Act
        result_doc = self.detector.detect_headings_in_document(document)
        
        # Assert
        assert result_doc.title == "Test Document"
        assert result_doc.metadata["author"] == "Test Author"
        assert result_doc.metadata["date"] == "2025-01-19"
    
    def test_extract_text_elements_from_blocks(self):
        """Test extraction of text elements from blocks."""
        # Arrange
        blocks = [
            TextBlock(content="Text 1", font_size=12.0),
            TextBlock(content="Text 2", font_size=14.0),
            TextBlock(content="Text without size", font_size=None),  # Should be skipped
        ]
        
        # Act
        elements = self.detector._extract_text_elements_from_blocks(blocks)
        
        # Assert
        assert len(elements) == 2  # Third block skipped due to no font_size
        assert elements[0].content == "Text 1"
        assert elements[0].font_size == 12.0
        assert elements[1].content == "Text 2"
        assert elements[1].font_size == 14.0
    
    def test_heading_detection_with_multiple_levels(self):
        """Test detection of multiple heading levels in one document."""
        # Arrange
        document = Document()
        # Add some normal text blocks first to establish baseline
        document.add_block(TextBlock(content="Normal text 1", font_size=12.0))       # Text
        document.add_block(TextBlock(content="Normal text 2", font_size=12.0))       # Text
        document.add_block(TextBlock(content="John Doe", font_size=24.0))            # H1: Name (content-aware)
        document.add_block(TextBlock(content="EXPERIENCE", font_size=21.6))          # H2: Major section
        document.add_block(TextBlock(content="EDUCATION", font_size=18.0))           # H2: Major section (content overrides font)
        document.add_block(TextBlock(content="SKILLS", font_size=15.6))              # H2: Major section (content overrides font)
        document.add_block(TextBlock(content="Normal text 3", font_size=12.0))       # Text
        
        # Act
        result_doc = self.detector.detect_headings_in_document(document)
        
        # Assert
        assert len(result_doc.blocks) == 7
        
        # Check that normal text stays as text
        assert isinstance(result_doc.blocks[0], TextBlock)
        assert isinstance(result_doc.blocks[1], TextBlock)
        
        # Check heading levels (content-aware resume detection)
        assert isinstance(result_doc.blocks[2], Heading) and result_doc.blocks[2].level == 1  # Name
        assert isinstance(result_doc.blocks[3], Heading) and result_doc.blocks[3].level == 2  # EXPERIENCE
        assert isinstance(result_doc.blocks[4], Heading) and result_doc.blocks[4].level == 2  # EDUCATION
        assert isinstance(result_doc.blocks[5], Heading) and result_doc.blocks[5].level == 2  # SKILLS
        assert isinstance(result_doc.blocks[6], TextBlock)