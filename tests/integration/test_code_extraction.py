"""
Integration tests for code block detection and extraction.

Tests end-to-end code block detection pipeline including:
- Code detector service integration
- Language detector integration  
- Pipeline integration in CLI
- Markdown output with code blocks
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from pdf2markdown.cli.main import PdfToMarkdownCli
from pdf2markdown.core.config import ApplicationConfig
from pdf2markdown.core.dependency_injection import create_default_container
from pdf2markdown.domain.models.document import Document, Line, CodeBlock, CodeLanguage, TextBlock
from pdf2markdown.domain.services.code_detector import CodeDetector
from pdf2markdown.domain.services.language_detector import LanguageDetector


class TestCodeExtractionIntegration:
    """Integration tests for code block extraction pipeline."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ApplicationConfig()
        self.container = create_default_container(self.config)
        
    def test_code_detector_integration_with_language_detector(self):
        """Test that code detector integrates properly with language detector."""
        # Create mock lines with monospace font
        lines = [
            Mock(text="def hello_world():", y_position=100.0, x_position=10.0, height=12.0, font_size=10.0, _font_family="Courier"),
            Mock(text="    print('Hello, World!')", y_position=88.0, x_position=14.0, height=12.0, font_size=10.0, _font_family="Courier"),
            Mock(text="    return True", y_position=76.0, x_position=14.0, height=12.0, font_size=10.0, _font_family="Courier")
        ]
        
        # Initialize detectors
        code_detector = CodeDetector()
        language_detector = LanguageDetector()
        
        # Detect code blocks
        code_blocks = code_detector.detect_code_blocks(lines)
        assert len(code_blocks) == 1
        
        # Analyze language
        code_block = code_blocks[0]
        analyzed_block = language_detector.analyze_code_block(code_block)
        
        # Verify integration
        assert analyzed_block.language == CodeLanguage.PYTHON
        assert "def hello_world" in analyzed_block.content
        assert "print('Hello, World!')" in analyzed_block.content
    
    def test_code_block_integration_in_document_processing(self):
        """Test code block detection integration with document creation and processing."""
        from pdf2markdown.cli.main import PdfToMarkdownCli
        
        # Test the integration by directly calling the _integrate_code_blocks_into_document method
        cli = PdfToMarkdownCli(config=self.config, container=self.container)
        
        # Create source document with various blocks
        source_document = Document(title="Test Document")
        source_document.add_block(TextBlock(content="Introduction text"))
        source_document.add_block(TextBlock(content="def hello(): print('hello')"))  # This should be replaced by code block
        source_document.add_block(TextBlock(content="Conclusion text"))
        
        # Create code blocks that should replace the middle text block
        lines = [
            Line("def hello():", 100.0, 10.0, 12.0),
            Line("    print('hello')", 88.0, 14.0, 12.0)
        ]
        code_block = CodeBlock(lines=lines, language=CodeLanguage.PYTHON)
        
        # Create target document
        target_document = Document(title="Test Document")
        
        # Test the integration method
        cli._integrate_code_blocks_into_document(
            target_document,
            source_document, 
            [code_block]
        )
        
        # Verify the integration worked correctly
        assert len(target_document.blocks) == 3  # Introduction + Code + Conclusion
        
        # Find the code block
        code_blocks = [block for block in target_document.blocks if isinstance(block, CodeBlock)]
        assert len(code_blocks) == 1
        assert code_blocks[0].language == CodeLanguage.PYTHON
        assert "def hello():" in code_blocks[0].content
        
        # Verify non-code text is preserved
        text_blocks = [block for block in target_document.blocks if isinstance(block, TextBlock)]
        text_contents = [block.content for block in text_blocks]
        assert "Introduction text" in text_contents
        assert "Conclusion text" in text_contents
        
        # Verify the code text was replaced (not duplicated)
        assert "def hello(): print('hello')" not in text_contents
    
    def test_code_block_markdown_output(self):
        """Test that detected code blocks are properly formatted in markdown."""
        # Create a code block
        lines = [
            Line("def fibonacci(n):", 100.0, 10.0, 12.0, font_size=10.0),
            Line("    if n <= 1:", 88.0, 14.0, 12.0, font_size=10.0),
            Line("        return n", 76.0, 18.0, 12.0, font_size=10.0),
        ]
        
        code_block = CodeBlock(lines=lines, language=CodeLanguage.PYTHON)
        
        # Test markdown conversion
        markdown = code_block.to_markdown()
        
        assert markdown.startswith("```python")
        assert "def fibonacci(n):" in markdown
        assert "    if n <= 1:" in markdown
        assert "        return n" in markdown
        assert markdown.endswith("```")
    
    def test_inline_code_detection(self):
        """Test inline code detection within paragraphs."""
        code_detector = CodeDetector()
        
        # Create mock line with font segments
        mock_line = Mock()
        mock_line._font_segments = [
            {
                'font_family': 'Times',
                'text': 'Use the ',
                'start': 0.0,
                'end': 8.0
            },
            {
                'font_family': 'Courier',
                'text': 'print()',
                'start': 8.0,
                'end': 15.0
            },
            {
                'font_family': 'Times', 
                'text': ' function.',
                'start': 15.0,
                'end': 25.0
            }
        ]
        
        # Detect inline code
        inline_codes = code_detector.detect_inline_code(mock_line)
        
        assert len(inline_codes) == 1
        assert inline_codes[0].content == 'print()'
        assert inline_codes[0].font_family == 'Courier'
    
    def test_code_language_detection_accuracy(self):
        """Test accuracy of language detection for different programming languages."""
        language_detector = LanguageDetector()
        
        test_cases = [
            ("def main():\n    print('Hello')\n    return 0", CodeLanguage.PYTHON),
            ("function test() {\n  console.log('Hello');\n  return true;\n}", CodeLanguage.JAVASCRIPT),
            ("public class Test {\n  public static void main(String[] args) {\n    System.out.println('Hello');\n  }\n}", CodeLanguage.JAVA),
            ("#include <iostream>\nint main() {\n  std::cout << 'Hello';\n  return 0;\n}", CodeLanguage.CPP),
            ("SELECT * FROM users WHERE name = 'test';", CodeLanguage.SQL),
            ("<html><body><h1>Hello</h1></body></html>", CodeLanguage.HTML),
            ('{"name": "test", "value": 42}', CodeLanguage.JSON)
        ]
        
        for code_content, expected_language in test_cases:
            detected_language = language_detector.detect_language(code_content)
            assert detected_language == expected_language, f"Failed to detect {expected_language.value} in: {code_content[:50]}..."
    
    def test_performance_code_detection(self):
        """Test that code detection meets performance requirements."""
        import time
        
        code_detector = CodeDetector()
        
        # Create many lines with code (simulating 10-page document)
        large_line_set = []
        for i in range(1000):
            large_line_set.append(
                Mock(
                    text=f"def function_{i}():",
                    y_position=1000.0 - i,
                    x_position=10.0,
                    height=12.0,
                    font_size=10.0,
                    _font_family="Courier"
                )
            )
        
        # Measure detection time
        start_time = time.time()
        code_blocks = code_detector.detect_code_blocks(large_line_set)
        end_time = time.time()
        
        detection_time = end_time - start_time
        
        # Should be well under 1 second for performance requirement
        assert detection_time < 1.0, f"Code detection took {detection_time:.2f}s, should be < 1.0s"
        assert len(code_blocks) > 0, "Should detect code blocks in large dataset"
    
    def test_cli_code_detection_integration_methods(self):
        """Test that CLI integration methods for code detection work correctly."""
        from pdf2markdown.cli.main import PdfToMarkdownCli
        
        cli = PdfToMarkdownCli(config=self.config, container=self.container)
        
        # Test the code integration method directly
        source_document = Document(title="Source")  
        source_document.add_block(TextBlock(content="Regular text"))
        source_document.add_block(TextBlock(content="function test() { return 42; }"))
        
        target_document = Document(title="Target")
        
        # Create code blocks with JavaScript
        lines = [
            Line("function test() {", 100.0, 10.0, 12.0),
            Line("  return 42;", 88.0, 14.0, 12.0),
            Line("}", 76.0, 10.0, 12.0)
        ]
        code_block = CodeBlock(lines=lines, language=CodeLanguage.JAVASCRIPT)
        
        # Call the integration method
        cli._integrate_code_blocks_into_document(target_document, source_document, [code_block])
        
        # Verify the integration
        assert len(target_document.blocks) == 2  # Regular text + code block
        code_blocks = [b for b in target_document.blocks if isinstance(b, CodeBlock)]
        assert len(code_blocks) == 1
        assert code_blocks[0].language == CodeLanguage.JAVASCRIPT
        
        # Test with no code blocks (edge case)
        target_document2 = Document(title="Target2")
        cli._integrate_code_blocks_into_document(target_document2, source_document, [])
        assert len(target_document2.blocks) == 2  # Both text blocks preserved
        
        # Test with empty source document (edge case)
        empty_source = Document(title="Empty")
        target_document3 = Document(title="Target3")
        cli._integrate_code_blocks_into_document(target_document3, empty_source, [code_block])
        assert len(target_document3.blocks) == 1  # Just the code block
        assert isinstance(target_document3.blocks[0], CodeBlock)

    def test_mixed_content_with_code_blocks(self):
        """Test document processing with mixed content including code blocks."""
        # This test verifies the integration handles documents with:
        # - Regular paragraphs
        # - Headings  
        # - Lists
        # - Code blocks
        # - Inline code
        
        code_detector = CodeDetector()
        
        # Mix of content types
        mixed_lines = [
            # Heading (non-monospace, large font)
            Mock(text="# Introduction", y_position=200.0, x_position=10.0, height=16.0, font_size=16.0, _font_family="Arial"),
            
            # Regular paragraph
            Mock(text="This document contains code examples.", y_position=180.0, x_position=10.0, height=12.0, font_size=12.0, _font_family="Arial"),
            
            # Code block
            Mock(text="def example():", y_position=160.0, x_position=10.0, height=12.0, font_size=10.0, _font_family="Courier"),
            Mock(text="    return 'Hello'", y_position=148.0, x_position=14.0, height=12.0, font_size=10.0, _font_family="Courier"),
            
            # More regular text
            Mock(text="The function above demonstrates Python syntax.", y_position=120.0, x_position=10.0, height=12.0, font_size=12.0, _font_family="Arial"),
        ]
        
        # Detect code blocks from mixed content
        code_blocks = code_detector.detect_code_blocks(mixed_lines)
        
        # Should detect the code block but not the heading or paragraphs
        assert len(code_blocks) == 1
        assert "def example():" in code_blocks[0].content
        assert "return 'Hello'" in code_blocks[0].content
        
        # Verify it's not detecting non-code content as code
        code_content = code_blocks[0].content
        assert "Introduction" not in code_content
        assert "This document contains" not in code_content
        assert "function above demonstrates" not in code_content