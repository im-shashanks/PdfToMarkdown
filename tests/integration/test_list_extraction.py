"""Integration tests for list detection in PDF processing pipeline."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pdf2markdown.cli.main import PdfToMarkdownCli
from pdf2markdown.core.config import ApplicationConfig, ListDetectionConfig
from pdf2markdown.core.dependency_injection import create_default_container
from pdf2markdown.domain.models.document import Document, Line, ListBlock, ListItem, ListMarker, ListType
from pdf2markdown.domain.services.list_detector import ListDetector
from pdf2markdown.infrastructure.formatters.markdown_formatter import MarkdownFormatter


class TestListExtractionIntegration:
    """Integration tests for list extraction functionality."""

    def test_list_detector_integration_with_formatter(self):
        """Test that list detection integrates properly with markdown formatting."""
        # Create test lines that represent list items
        lines = [
            Line("• First bullet item", 100.0, 50.0, 12.0),
            Line("• Second bullet item", 85.0, 50.0, 12.0),
            Line("1. First numbered item", 70.0, 50.0, 12.0),
            Line("2. Second numbered item", 55.0, 50.0, 12.0),
        ]
        
        # Create list detector and detect items
        detector = ListDetector()
        list_items = detector.detect_list_items_from_lines(lines)
        list_blocks = detector.group_list_items_into_blocks(list_items)
        
        # Create document with list blocks
        document = Document()
        for block in list_blocks:
            document.add_block(block)
        
        # Format to markdown
        formatter = MarkdownFormatter()
        markdown = formatter.format_document(document)
        
        # Verify markdown output
        expected_lines = [
            "- First bullet item",
            "- Second bullet item", 
            "1. First numbered item",
            "2. Second numbered item"
        ]
        
        for expected_line in expected_lines:
            assert expected_line in markdown

    def test_nested_list_integration(self):
        """Test nested list detection and formatting."""
        lines = [
            Line("1. Parent item", 100.0, 50.0, 12.0),
            Line("  • Nested bullet", 85.0, 60.0, 12.0),  # Indented
            Line("  • Another nested", 70.0, 60.0, 12.0),  # Indented
            Line("2. Second parent", 55.0, 50.0, 12.0),
        ]
        
        detector = ListDetector()
        list_items = detector.detect_list_items_from_lines(lines)
        list_blocks = detector.group_list_items_into_blocks(list_items)
        
        # Should detect mixed nesting
        assert len(list_blocks) > 0
        
        # Verify nesting levels are detected
        found_nested = any(
            any(item.level > 0 for item in block.items)
            for block in list_blocks
        )
        assert found_nested, "Should detect nested list items"
        
        # Test markdown formatting
        document = Document()
        for block in list_blocks:
            document.add_block(block)
        
        formatter = MarkdownFormatter()
        markdown = formatter.format_document(document)
        
        # Should contain indented items
        assert "  - " in markdown or "  • " in markdown

    def test_mixed_list_types_integration(self):
        """Test handling of mixed list types (bullets and numbers)."""
        lines = [
            Line("• Bullet item 1", 100.0, 50.0, 12.0),
            Line("• Bullet item 2", 85.0, 50.0, 12.0),
            Line("Regular paragraph text", 70.0, 50.0, 12.0),
            Line("1. Numbered item 1", 55.0, 50.0, 12.0),
            Line("2. Numbered item 2", 40.0, 50.0, 12.0),
        ]
        
        detector = ListDetector()
        list_items = detector.detect_list_items_from_lines(lines)
        list_blocks = detector.group_list_items_into_blocks(list_items)
        
        # Should create separate blocks for different list types
        unordered_blocks = [b for b in list_blocks if b.list_type == ListType.UNORDERED]
        ordered_blocks = [b for b in list_blocks if b.list_type == ListType.ORDERED]
        
        assert len(unordered_blocks) >= 1, "Should detect unordered list"
        assert len(ordered_blocks) >= 1, "Should detect ordered list"
        
        # Test that both list types format correctly
        document = Document()
        for block in list_blocks:
            document.add_block(block)
        
        formatter = MarkdownFormatter()
        markdown = formatter.format_document(document)
        
        assert "- Bullet item 1" in markdown
        assert "1. Numbered item 1" in markdown

    def test_list_continuation_integration(self):
        """Test list item continuation across multiple lines."""
        lines = [
            Line("1. This is a long list item that", 100.0, 50.0, 12.0),
            Line("   continues on the next line", 85.0, 60.0, 12.0),  # Continuation
            Line("2. Second item", 70.0, 50.0, 12.0),
        ]
        
        detector = ListDetector()
        list_items = detector.detect_list_items_from_lines(lines)
        
        # Should merge continuation lines
        assert len(list_items) == 2, "Should detect 2 list items"
        
        # First item should contain continuation text
        first_item = list_items[0]
        assert "continues on the next line" in first_item.content
        
        # Test formatting preserves continuation
        list_blocks = detector.group_list_items_into_blocks(list_items)
        document = Document()
        for block in list_blocks:
            document.add_block(block)
        
        formatter = MarkdownFormatter()
        markdown = formatter.format_document(document)
        
        # Should contain the full continued text
        assert "continues on the next line" in markdown

    def test_complex_list_patterns_integration(self):
        """Test various complex list marker patterns."""
        lines = [
            Line("a. Alphabetic item", 100.0, 50.0, 12.0),
            Line("b. Second alphabetic", 85.0, 50.0, 12.0),
            Line("i. Roman numeral", 70.0, 50.0, 12.0),
            Line("ii. Second roman", 55.0, 50.0, 12.0),
            Line("(1) Parenthetical", 40.0, 50.0, 12.0),
            Line("(2) Second parenthetical", 25.0, 50.0, 12.0),
        ]
        
        detector = ListDetector()
        list_items = detector.detect_list_items_from_lines(lines)
        list_blocks = detector.group_list_items_into_blocks(list_items)
        
        # Should detect all as ordered lists in a single continuous block
        assert len(list_blocks) >= 1, "Should create at least one ordered list block"
        
        # All should be ordered lists
        for block in list_blocks:
            assert block.list_type == ListType.ORDERED
            assert len(block.items) >= 1
        
        # Should detect all 6 items total
        total_items = sum(len(block.items) for block in list_blocks)
        assert total_items == 6, f"Should detect all 6 list items, got {total_items}"

    def test_dependency_injection_configuration(self):
        """Test that dependency injection properly configures list detection."""
        # Create config with custom list detection settings
        config = ApplicationConfig(
            list_detection=ListDetectionConfig(
                indentation_threshold=15.0,
                max_nesting_level=2,
                enable_bullet_detection=True,
                enable_numbered_detection=True
            )
        )
        
        # Create container with custom config
        container = create_default_container(config)
        
        # Resolve list detector and verify configuration
        from pdf2markdown.domain.interfaces import ListDetectorInterface
        list_detector = container.resolve(ListDetectorInterface)
        
        assert isinstance(list_detector, ListDetector)
        assert list_detector.indentation_threshold == 15.0
        assert list_detector.max_nesting_level == 2

    def test_performance_with_many_list_items(self):
        """Test performance with a large number of list items."""
        import time
        
        # Create many list items
        lines = []
        for i in range(100):
            y_pos = 1000.0 - (i * 15.0)  # Spread vertically
            lines.append(Line(f"• Item {i+1}", y_pos, 50.0, 12.0))
        
        detector = ListDetector()
        
        # Measure detection time
        start_time = time.time()
        list_items = detector.detect_list_items_from_lines(lines)
        list_blocks = detector.group_list_items_into_blocks(list_items)
        end_time = time.time()
        
        # Should complete quickly
        detection_time = end_time - start_time
        assert detection_time < 1.0, f"Detection took {detection_time:.3f}s, should be under 1 second"
        
        # Should detect all items
        assert len(list_items) == 100
        assert len(list_blocks) == 1  # Single unordered list
        
        # Test markdown generation performance
        document = Document()
        for block in list_blocks:
            document.add_block(block)
        
        formatter = MarkdownFormatter()
        
        start_time = time.time()
        markdown = formatter.format_document(document)
        end_time = time.time()
        
        formatting_time = end_time - start_time
        assert formatting_time < 0.5, f"Formatting took {formatting_time:.3f}s, should be under 0.5 seconds"
        
        # Verify output contains all items
        for i in range(100):
            assert f"- Item {i+1}" in markdown

    def test_empty_and_edge_cases_integration(self):
        """Test edge cases in integration."""
        detector = ListDetector()
        
        # Empty lines
        empty_result = detector.detect_list_items_from_lines([])
        assert empty_result == []
        
        # Lines with no list markers
        non_list_lines = [
            Line("Regular paragraph text", 100.0, 50.0, 12.0),
            Line("Another regular line", 85.0, 50.0, 12.0),
        ]
        
        no_lists = detector.detect_list_items_from_lines(non_list_lines)
        assert no_lists == []
        
        # Single list item
        single_item_lines = [Line("• Single item", 100.0, 50.0, 12.0)]
        single_result = detector.detect_list_items_from_lines(single_item_lines)
        assert len(single_result) == 1
        assert single_result[0].content == "Single item"

    def test_configuration_integration(self):
        """Test that configuration properly affects list detection behavior."""
        lines = [
            Line("• Level 0", 100.0, 50.0, 12.0),
            Line("  • Level 1", 85.0, 60.0, 12.0),  # Indented 10 points
            Line("    • Level 2", 70.0, 70.0, 12.0),  # Indented 20 points
        ]
        
        # Test with different indentation thresholds
        detector_strict = ListDetector(indentation_threshold=5.0)
        items_strict = detector_strict.detect_list_items_from_lines(lines)
        
        detector_loose = ListDetector(indentation_threshold=15.0)
        items_loose = detector_loose.detect_list_items_from_lines(lines)
        
        # Strict detector should detect more levels
        max_level_strict = max(item.level for item in items_strict)
        max_level_loose = max(item.level for item in items_loose)
        
        assert max_level_strict >= max_level_loose
        
        # Test max nesting level limits
        detector_limited = ListDetector(max_nesting_level=1)
        items_limited = detector_limited.detect_list_items_from_lines(lines)
        
        max_level_limited = max(item.level for item in items_limited)
        assert max_level_limited <= 1