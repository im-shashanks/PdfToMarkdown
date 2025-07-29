"""
Unit tests for CodeDetector service.

Following TDD methodology - Red phase: Create failing tests first.
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import List, Dict, Any

from pdf2markdown.domain.models.document import Line, CodeBlock, CodeLanguage, CodeStyle, InlineCode
from pdf2markdown.domain.services.code_detector import CodeDetector


@dataclass
class MockLine:
    """Mock version of Line with mutable attributes for font information."""
    text: str
    y_position: float
    x_position: float
    height: float
    font_size: float = 10.0
    _font_family: str = ""
    _font_segments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self._font_segments is None:
            self._font_segments = []


class TestCodeDetector:
    """Test CodeDetector domain service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = CodeDetector()
    
    def test_is_monospace_font_common_families(self):
        """Test recognition of common monospace font families."""
        # Common system monospace fonts
        assert self.detector.is_monospace_font("Courier") is True
        assert self.detector.is_monospace_font("Courier New") is True
        assert self.detector.is_monospace_font("Monaco") is True
        assert self.detector.is_monospace_font("Menlo") is True
        
        # Programming fonts
        assert self.detector.is_monospace_font("Consolas") is True
        assert self.detector.is_monospace_font("Inconsolata") is True
        assert self.detector.is_monospace_font("Source Code Pro") is True
        assert self.detector.is_monospace_font("Fira Code") is True
        
        # Non-monospace fonts
        assert self.detector.is_monospace_font("Arial") is False
        assert self.detector.is_monospace_font("Times New Roman") is False
        assert self.detector.is_monospace_font("Helvetica") is False
    
    def test_is_monospace_font_case_insensitive(self):
        """Test that font recognition is case insensitive."""
        assert self.detector.is_monospace_font("courier") is True
        assert self.detector.is_monospace_font("COURIER NEW") is True
        assert self.detector.is_monospace_font("Consolas") is True
        assert self.detector.is_monospace_font("consolas") is True
    
    def test_is_monospace_font_partial_matching(self):
        """Test that partial font names are matched correctly."""
        # Should match fonts that contain monospace names
        assert self.detector.is_monospace_font("Courier-Bold") is True
        assert self.detector.is_monospace_font("Monaco-Regular") is True
        
        # Should not match unrelated fonts
        assert self.detector.is_monospace_font("Times") is False
        assert self.detector.is_monospace_font("Unknown Font") is False
    
    def test_analyze_font_characteristics_consistent_monospace(self):
        """Test font characteristics analysis with consistent monospace text."""
        # Create lines with consistent character widths (simulating monospace)
        lines = [
            MockLine("def function():", 100.0, 10.0, 12.0, font_size=10.0, _font_family="Courier New"),
            MockLine("    return 42", 88.0, 14.0, 12.0, font_size=10.0, _font_family="Courier New"),
            MockLine("}", 76.0, 10.0, 12.0, font_size=10.0, _font_family="Courier New")
        ]
        
        assert self.detector.analyze_font_characteristics(lines) is True
    
    def test_analyze_font_characteristics_mixed_fonts(self):
        """Test font characteristics analysis with mixed font types."""
        lines = [
            MockLine("Regular text in Arial", 100.0, 10.0, 12.0, font_size=10.0, _font_family="Arial"),
            MockLine("def function():", 88.0, 10.0, 12.0, font_size=10.0, _font_family="Courier New"),
            MockLine("More regular text", 76.0, 10.0, 12.0, font_size=10.0, _font_family="Arial")
        ]
        
        assert self.detector.analyze_font_characteristics(lines) is False
    
    def test_detect_code_blocks_simple_python(self):
        """Test detection of a simple Python code block."""
        lines = [
            MockLine("def hello_world():", 100.0, 10.0, 12.0, font_size=10.0, _font_family="Courier New"),
            MockLine("    print('Hello, World!')", 88.0, 14.0, 12.0, font_size=10.0, _font_family="Courier New"),
            MockLine("    return True", 76.0, 14.0, 12.0, font_size=10.0, _font_family="Courier New")
        ]
        
        code_blocks = self.detector.detect_code_blocks(lines)
        
        assert len(code_blocks) == 1
        assert isinstance(code_blocks[0], CodeBlock)
        assert len(code_blocks[0].lines) == 3
        assert code_blocks[0].language == CodeLanguage.UNKNOWN  # Language detection happens separately
    
    def test_detect_code_blocks_multiple_blocks(self):
        """Test detection of multiple separate code blocks."""
        lines = [
            MockLine("# First code block", 120.0, 10.0, 12.0, font_size=10.0, _font_family="Arial"),
            MockLine("def func1():", 108.0, 10.0, 12.0, font_size=10.0, _font_family="Monaco"),
            MockLine("    pass", 96.0, 14.0, 12.0, font_size=10.0, _font_family="Monaco"),
            MockLine("", 84.0, 10.0, 12.0, font_size=10.0, _font_family="Arial"),  # Empty line separator
            MockLine("# Second code block", 72.0, 10.0, 12.0, font_size=10.0, _font_family="Arial"),
            MockLine("def func2():", 60.0, 10.0, 12.0, font_size=10.0, _font_family="Monaco"),
            MockLine("    return 42", 48.0, 14.0, 12.0, font_size=10.0, _font_family="Monaco")
        ]
        
        code_blocks = self.detector.detect_code_blocks(lines)
        
        assert len(code_blocks) == 2
        assert len(code_blocks[0].lines) == 2  # func1 definition and pass
        assert len(code_blocks[1].lines) == 2  # func2 definition and return
    
    def test_detect_code_blocks_empty_input(self):
        """Test code block detection with empty input."""
        code_blocks = self.detector.detect_code_blocks([])
        assert code_blocks == []
    
    def test_detect_code_blocks_no_monospace(self):
        """Test code block detection with no monospace text."""
        lines = [
            MockLine("Regular paragraph text", 100.0, 10.0, 12.0, font_size=10.0, _font_family="Arial"),
            MockLine("More regular text", 88.0, 10.0, 12.0, font_size=10.0, _font_family="Arial")
        ]
        
        code_blocks = self.detector.detect_code_blocks(lines)
        assert code_blocks == []
    
    def test_detect_inline_code_simple(self):
        """Test detection of simple inline code within text."""
        line = MockLine(
            "The variable `count` should be incremented.", 
            100.0, 10.0, 12.0, font_size=10.0,
            _font_segments=[
                {"text": "The variable ", "font_family": "Arial", "start": 0.0, "end": 13.0},
                {"text": "count", "font_family": "Courier New", "start": 13.0, "end": 18.0},
                {"text": " should be incremented.", "font_family": "Arial", "start": 18.0, "end": 41.0}
            ]
        )
        
        inline_codes = self.detector.detect_inline_code(line)
        
        assert len(inline_codes) == 1
        assert inline_codes[0].content == "count"
        assert inline_codes[0].font_family == "Courier New"
        assert inline_codes[0].start_position == 13.0
        assert inline_codes[0].end_position == 18.0
    
    def test_detect_inline_code_multiple_segments(self):
        """Test detection of multiple inline code segments in one line."""
        line = MockLine(
            "Use `print()` and `input()` functions.", 
            100.0, 10.0, 12.0, font_size=10.0,
            _font_segments=[
                {"text": "Use ", "font_family": "Arial", "start": 0.0, "end": 4.0},
                {"text": "print()", "font_family": "Monaco", "start": 4.0, "end": 11.0},
                {"text": " and ", "font_family": "Arial", "start": 11.0, "end": 16.0},
                {"text": "input()", "font_family": "Monaco", "start": 16.0, "end": 23.0},
                {"text": " functions.", "font_family": "Arial", "start": 23.0, "end": 34.0}
            ]
        )
        
        inline_codes = self.detector.detect_inline_code(line)
        
        assert len(inline_codes) == 2
        assert inline_codes[0].content == "print()"
        assert inline_codes[1].content == "input()"
    
    def test_detect_inline_code_no_monospace(self):
        """Test inline code detection with no monospace segments."""
        line = MockLine(
            "Regular text with no code", 
            100.0, 10.0, 12.0, font_size=10.0,
            _font_segments=[
                {"text": "Regular text with no code", "font_family": "Arial", "start": 0.0, "end": 25.0}
            ]
        )
        
        inline_codes = self.detector.detect_inline_code(line)
        assert inline_codes == []
    
    def test_detect_inline_code_too_long(self):
        """Test that very long monospace segments are not considered inline code."""
        line = MockLine(
            "This is a very long monospace segment that should be a code block", 
            100.0, 10.0, 12.0, font_size=10.0,
            _font_segments=[
                {"text": "This is a very long monospace segment that should be a code block", "font_family": "Courier", "start": 0.0, "end": 66.0}
            ]
        )
        
        inline_codes = self.detector.detect_inline_code(line)
        assert inline_codes == []  # Too long for inline code
    
    def test_is_code_context_surrounded_by_code(self):
        """Test code context detection when line is surrounded by code."""
        lines = [
            MockLine("def function():", 100.0, 10.0, 12.0, font_size=10.0, _font_family="Monaco"),
            MockLine("    # This is a comment", 88.0, 14.0, 12.0, font_size=10.0, _font_family="Monaco"),  # Target line
            MockLine("    return 42", 76.0, 14.0, 12.0, font_size=10.0, _font_family="Monaco")
        ]
        
        assert self.detector.is_code_context(lines, 1) is True
    
    def test_is_code_context_isolated_monospace_header(self):
        """Test that isolated monospace text (like headers) is not considered code context."""
        lines = [
            MockLine("Regular paragraph text", 120.0, 10.0, 12.0, font_size=10.0, _font_family="Arial"),
            MockLine("MONOSPACE HEADER", 100.0, 10.0, 16.0, font_size=16.0, _font_family="Courier New"),  # Target line - larger font
            MockLine("More regular text", 88.0, 10.0, 12.0, font_size=10.0, _font_family="Arial")
        ]
        
        assert self.detector.is_code_context(lines, 1) is False
    
    def test_is_code_context_edge_cases(self):
        """Test code context detection edge cases."""
        # First line
        lines = [MockLine("def func():", 100.0, 10.0, 12.0, font_size=10.0, _font_family="Monaco")]
        assert self.detector.is_code_context(lines, 0) is True
        
        # Empty lines list
        assert self.detector.is_code_context([], 0) is False
        
        # Invalid index
        assert self.detector.is_code_context(lines, 5) is False
    
    def test_constructor_with_configuration(self):
        """Test CodeDetector constructor with configuration options."""
        config = {
            'monospace_fonts': ['CustomFont'],
            'max_inline_code_length': 50,
            'character_width_threshold': 0.1
        }
        
        detector = CodeDetector(config)
        assert detector.is_monospace_font("CustomFont") is True
        assert detector.is_monospace_font("Arial") is False
    
    def test_detect_code_blocks_preserves_style_info(self):
        """Test that code block detection preserves style information."""
        lines = [
            MockLine("def test():", 100.0, 10.0, 12.0, font_size=10.0, _font_family="Fira Code"),
            MockLine("    pass", 88.0, 14.0, 12.0, font_size=10.0, _font_family="Fira Code")
        ]
        
        code_blocks = self.detector.detect_code_blocks(lines)
        
        assert len(code_blocks) == 1
        code_block = code_blocks[0]
        assert code_block.style is not None
        assert code_block.style.font_family == "Fira Code"
        assert code_block.style.indentation_level > 0  # Should detect indentation
    
    def test_performance_with_large_input(self):
        """Test that code detection performs well with large inputs."""
        # Create 1000 lines to test performance
        lines = []
        for i in range(1000):
            lines.append(MockLine(f"line {i} content", 1000.0 - i, 10.0, 12.0, font_size=10.0, _font_family="Arial"))
        
        # This should complete quickly
        import time
        start_time = time.time()
        code_blocks = self.detector.detect_code_blocks(lines)
        duration = time.time() - start_time
        
        assert duration < 1.0  # Should complete in under 1 second
        assert code_blocks == []  # No monospace content