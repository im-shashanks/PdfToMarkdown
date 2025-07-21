"""Unit tests for ListDetector service."""

import pytest

from pdf2markdown.domain.models.document import Line, ListType, ListMarker, ListItem
from pdf2markdown.domain.services.list_detector import ListDetector


class TestListDetector:
    """Test cases for ListDetector service."""

    @pytest.fixture
    def detector(self):
        """Create a ListDetector instance for testing."""
        return ListDetector()

    def test_detect_bullet_markers(self, detector):
        """Test detection of various bullet point markers."""
        # Standard bullet points
        bullet_tests = [
            ("• First item", "•"),
            ("◦ Second item", "◦"), 
            ("▪ Third item", "▪"),
            ("▫ Fourth item", "▫"),
            ("■ Fifth item", "■"),
            ("□ Sixth item", "□"),
            ("- Dash item", "-"),
            ("* Asterisk item", "*"),
            ("+ Plus item", "+"),
        ]
        
        for text, expected_symbol in bullet_tests:
            line = Line(text, 100.0, 50.0, 12.0)
            marker = detector.detect_list_marker(line)
            
            assert marker is not None, f"Failed to detect marker in '{text}'"
            assert marker.marker_type == ListType.UNORDERED
            assert marker.symbol == expected_symbol
            assert marker.prefix == ""
            assert marker.suffix == " "

    def test_detect_numbered_markers(self, detector):
        """Test detection of numbered list markers."""
        numbered_tests = [
            ("1. First item", "1", "", ". "),
            ("2. Second item", "2", "", ". "),
            ("10. Tenth item", "10", "", ". "),
            ("1) First item", "1", "", ") "),
            ("2) Second item", "2", "", ") "),
            ("10) Tenth item", "10", "", ") "),
        ]
        
        for text, expected_symbol, expected_prefix, expected_suffix in numbered_tests:
            line = Line(text, 100.0, 50.0, 12.0)
            marker = detector.detect_list_marker(line)
            
            assert marker is not None, f"Failed to detect marker in '{text}'"
            assert marker.marker_type == ListType.ORDERED
            assert marker.symbol == expected_symbol
            assert marker.prefix == expected_prefix
            assert marker.suffix == expected_suffix

    def test_detect_alphabetic_markers(self, detector):
        """Test detection of alphabetic list markers."""
        alpha_tests = [
            ("a. First item", "a", "", ". "),
            ("b. Second item", "b", "", ". "),
            ("z. Last item", "z", "", ". "),
            ("A. First item", "A", "", ". "),
            ("B. Second item", "B", "", ". "),
            ("Z. Last item", "Z", "", ". "),
        ]
        
        for text, expected_symbol, expected_prefix, expected_suffix in alpha_tests:
            line = Line(text, 100.0, 50.0, 12.0)
            marker = detector.detect_list_marker(line)
            
            assert marker is not None, f"Failed to detect marker in '{text}'"
            assert marker.marker_type == ListType.ORDERED
            assert marker.symbol == expected_symbol
            assert marker.prefix == expected_prefix
            assert marker.suffix == expected_suffix

    def test_detect_roman_numeral_markers(self, detector):
        """Test detection of roman numeral markers."""
        roman_tests = [
            ("i. First item", "i", "", ". "),
            ("ii. Second item", "ii", "", ". "),
            ("iii. Third item", "iii", "", ". "),
            ("iv. Fourth item", "iv", "", ". "),
            ("v. Fifth item", "v", "", ". "),
            ("I. First item", "I", "", ". "),
            ("II. Second item", "II", "", ". "),
            ("III. Third item", "III", "", ". "),
            ("IV. Fourth item", "IV", "", ". "),
            ("V. Fifth item", "V", "", ". "),
        ]
        
        for text, expected_symbol, expected_prefix, expected_suffix in roman_tests:
            line = Line(text, 100.0, 50.0, 12.0)
            marker = detector.detect_list_marker(line)
            
            assert marker is not None, f"Failed to detect marker in '{text}'"
            assert marker.marker_type == ListType.ORDERED
            assert marker.symbol == expected_symbol
            assert marker.prefix == expected_prefix
            assert marker.suffix == expected_suffix

    def test_detect_parenthetical_markers(self, detector):
        """Test detection of parenthetical list markers."""
        paren_tests = [
            ("(1) First item", "1", "(", ") "),
            ("(2) Second item", "2", "(", ") "),
            ("(a) First item", "a", "(", ") "),
            ("(b) Second item", "b", "(", ") "),
            ("(i) First item", "i", "(", ") "),
            ("(ii) Second item", "ii", "(", ") "),
        ]
        
        for text, expected_symbol, expected_prefix, expected_suffix in paren_tests:
            line = Line(text, 100.0, 50.0, 12.0)
            marker = detector.detect_list_marker(line)
            
            assert marker is not None, f"Failed to detect marker in '{text}'"
            assert marker.marker_type == ListType.ORDERED
            assert marker.symbol == expected_symbol
            assert marker.prefix == expected_prefix
            assert marker.suffix == expected_suffix

    def test_no_marker_detection(self, detector):
        """Test that non-list lines are not detected as having markers."""
        non_list_lines = [
            "Regular paragraph text",
            "Another line of text",
            "Text with numbers 1 and 2 but not a list",
            "Text with dash - but not at start",
            "  Indented text without marker",
            "",
            "HEADING TEXT",
            "123 Main Street",  # Address, not list
        ]
        
        for text in non_list_lines:
            line = Line(text, 100.0, 50.0, 12.0)
            marker = detector.detect_list_marker(line)
            assert marker is None, f"Incorrectly detected marker in '{text}'"

    def test_is_list_marker_line(self, detector):
        """Test checking if line contains a list marker."""
        list_lines = [
            "• Bullet item",
            "1. Numbered item", 
            "a. Alpha item",
            "i. Roman item",
            "(1) Paren item"
        ]
        
        for text in list_lines:
            line = Line(text, 100.0, 50.0, 12.0)
            assert detector.is_list_marker_line(line), f"Failed to identify '{text}' as list marker line"

        non_list_lines = [
            "Regular text",
            "Text with 1. in middle",
            "  Indented without marker"
        ]
        
        for text in non_list_lines:
            line = Line(text, 100.0, 50.0, 12.0)
            assert not detector.is_list_marker_line(line), f"Incorrectly identified '{text}' as list marker line"

    def test_detect_indented_markers(self, detector):
        """Test detection of indented list markers."""
        indented_tests = [
            ("  • Indented bullet", "•", 1),  # Level 1
            ("    ◦ Double indented", "◦", 2),  # Level 2
            ("      ▪ Triple indented", "▪", 3),  # Level 3
            ("  1. Indented number", "1", 1),  # Level 1 ordered
            ("    a. Double indent alpha", "a", 2),  # Level 2 ordered
        ]
        
        for text, expected_symbol, expected_level in indented_tests:
            line = Line(text, 100.0, 52.0 + (expected_level * 10), 12.0)  # Simulate indentation via x-position
            marker = detector.detect_list_marker(line)
            
            assert marker is not None, f"Failed to detect indented marker in '{text}'"
            assert marker.symbol == expected_symbol

    def test_detect_list_items_from_lines(self, detector):
        """Test detection of list items from multiple lines."""
        lines = [
            Line("• First bullet item", 100.0, 50.0, 12.0),
            Line("• Second bullet item", 85.0, 50.0, 12.0),
            Line("  with continuation", 70.0, 55.0, 12.0),  # Continuation line
            Line("• Third bullet item", 55.0, 50.0, 12.0),
        ]
        
        list_items = detector.detect_list_items_from_lines(lines)
        
        assert len(list_items) == 3  # Three list items
        assert list_items[0].content == "First bullet item"
        assert list_items[1].content == "Second bullet item with continuation"
        assert list_items[2].content == "Third bullet item"
        
        # Check that all items have correct markers
        for item in list_items:
            assert item.marker.marker_type == ListType.UNORDERED
            assert item.marker.symbol == "•"

    def test_group_list_items_into_blocks(self, detector):
        """Test grouping list items into coherent blocks."""
        # Create list items of different types
        marker_bullet = ListMarker(ListType.UNORDERED, "•", "", " ")
        marker_number = ListMarker(ListType.ORDERED, "1", "", ". ")
        
        list_items = [
            ListItem("First bullet", 0, marker_bullet),
            ListItem("Second bullet", 0, marker_bullet),
            ListItem("First numbered", 0, marker_number),
            ListItem("Second numbered", 0, marker_number),
            ListItem("Third bullet", 0, marker_bullet),
        ]
        
        blocks = detector.group_list_items_into_blocks(list_items)
        
        # Should create 3 blocks: bullet, numbered, bullet
        assert len(blocks) == 3
        assert blocks[0].list_type == ListType.UNORDERED
        assert len(blocks[0].items) == 2
        assert blocks[1].list_type == ListType.ORDERED
        assert len(blocks[1].items) == 2
        assert blocks[2].list_type == ListType.UNORDERED
        assert len(blocks[2].items) == 1

    def test_nested_list_detection(self, detector):
        """Test detection of nested list structures."""
        lines = [
            Line("1. First item", 100.0, 50.0, 12.0),
            Line("  • Nested bullet", 85.0, 55.0, 12.0),  # Indented
            Line("  • Another nested", 70.0, 55.0, 12.0),  # Indented  
            Line("2. Second item", 55.0, 50.0, 12.0),
            Line("    a. Deep nested", 40.0, 65.0, 12.0),  # More indented
        ]
        
        list_items = detector.detect_list_items_from_lines(lines)
        
        # Should detect nesting levels based on indentation
        assert len(list_items) == 5
        assert list_items[0].level == 0  # "1. First item"
        assert list_items[1].level == 1  # "• Nested bullet"
        assert list_items[2].level == 1  # "• Another nested"
        assert list_items[3].level == 0  # "2. Second item"
        assert list_items[4].level == 2  # "a. Deep nested"

    def test_complex_list_patterns(self, detector):
        """Test detection of complex list patterns."""
        # Test edge cases and complex patterns
        edge_cases = [
            ("1.5. Not a list", None),  # Decimal number
            ("1.. Double dot", None),   # Double dot
            ("a.. Double dot alpha", None),
            (".1 Dot first", None),    # Dot before number
            ("•No space", None),       # No space after bullet
            ("1.No space", None),      # No space after number
            ("• ", "•"),               # Just marker and space
            ("1. ", "1"),              # Just number and space
        ]
        
        for text, expected_symbol in edge_cases:
            line = Line(text, 100.0, 50.0, 12.0)
            marker = detector.detect_list_marker(line)
            
            if expected_symbol is None:
                assert marker is None, f"Incorrectly detected marker in '{text}'"
            else:
                assert marker is not None, f"Failed to detect marker in '{text}'"
                assert marker.symbol == expected_symbol

    def test_list_continuation_detection(self, detector):
        """Test detection of list item continuation across lines."""
        lines = [
            Line("1. This is a long list item that", 100.0, 50.0, 12.0),
            Line("   continues on the next line", 85.0, 55.0, 12.0),  # Continuation
            Line("   and even another line", 70.0, 55.0, 12.0),      # Another continuation
            Line("2. This is the second item", 55.0, 50.0, 12.0),    # New item
        ]
        
        list_items = detector.detect_list_items_from_lines(lines)
        
        assert len(list_items) == 2
        # First item should include all continuation text
        expected_content = "This is a long list item that continues on the next line and even another line"
        assert list_items[0].content == expected_content
        assert list_items[1].content == "This is the second item"
        
        # Both should be at level 0
        assert list_items[0].level == 0
        assert list_items[1].level == 0