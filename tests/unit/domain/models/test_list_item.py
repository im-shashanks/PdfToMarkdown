"""Unit tests for ListItem value object."""

import pytest

from pdf2markdown.domain.models.document import Line
from pdf2markdown.domain.models.document import ListItem
from pdf2markdown.domain.models.document import ListMarker
from pdf2markdown.domain.models.document import ListType


class TestListItemCreation:
    """Test cases for ListItem creation and validation."""

    def test_create_basic_list_item(self):
        """Test creating a basic list item."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item = ListItem(
            content="Basic list item",
            level=0,
            marker=marker
        )
        
        assert item.content == "Basic list item"
        assert item.level == 0
        assert item.marker == marker
        assert item.lines == []

    def test_create_list_item_with_lines(self):
        """Test creating a list item with line data."""
        marker = ListMarker(ListType.ORDERED, "1", "", ". ")
        lines = [
            Line("1. First line of item", 100.0, 50.0, 12.0),
            Line("   continued on next line", 85.0, 50.0, 12.0)
        ]
        
        item = ListItem(
            content="First line of item continued on next line",
            level=0,
            marker=marker,
            lines=lines
        )
        
        assert len(item.lines) == 2
        assert item.lines[0].text == "1. First line of item"
        assert item.lines[1].text == "   continued on next line"

    def test_create_nested_list_items(self):
        """Test creating list items at different nesting levels."""
        # Level 0 item
        marker0 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item0 = ListItem("Top level", 0, marker0)
        assert item0.level == 0
        
        # Level 1 item
        marker1 = ListMarker(ListType.UNORDERED, "◦", "", " ")
        item1 = ListItem("First nested", 1, marker1)
        assert item1.level == 1
        
        # Level 2 item
        marker2 = ListMarker(ListType.UNORDERED, "▪", "", " ")
        item2 = ListItem("Second nested", 2, marker2)
        assert item2.level == 2
        
        # Level 3 item (maximum)
        marker3 = ListMarker(ListType.UNORDERED, "▫", "", " ")
        item3 = ListItem("Third nested", 3, marker3)
        assert item3.level == 3


class TestListItemValidation:
    """Test cases for ListItem validation rules."""

    def test_negative_level_validation(self):
        """Test that negative levels are rejected."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        
        with pytest.raises(ValueError, match="level must be non-negative"):
            ListItem("Test", -1, marker)

    def test_maximum_level_validation(self):
        """Test that levels above maximum are rejected."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        
        # Level 3 should work (maximum)
        item3 = ListItem("Test", 3, marker)
        assert item3.level == 3
        
        # Level 4 should fail
        with pytest.raises(ValueError, match="level cannot exceed 3"):
            ListItem("Test", 4, marker)
        
        # Level 5 should also fail
        with pytest.raises(ValueError, match="level cannot exceed 3"):
            ListItem("Test", 5, marker)

    def test_empty_content_validation(self):
        """Test that empty content is rejected."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        
        with pytest.raises(ValueError, match="content cannot be empty"):
            ListItem("", 0, marker)
        
        with pytest.raises(ValueError, match="content cannot be empty"):
            ListItem("   ", 0, marker)  # Whitespace only
        
        with pytest.raises(ValueError, match="content cannot be empty"):
            ListItem("\n\t", 0, marker)  # Whitespace characters

    def test_marker_type_validation(self):
        """Test that marker must be a ListMarker instance."""
        with pytest.raises(TypeError, match="marker must be a ListMarker"):
            ListItem("Test", 0, "not a marker")

    def test_lines_type_validation(self):
        """Test that lines must be a list of Line objects."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        
        # Should accept empty list
        item1 = ListItem("Test", 0, marker, lines=[])
        assert item1.lines == []
        
        # Should accept list of Line objects
        lines = [Line("Test line", 100.0, 50.0, 12.0)]
        item2 = ListItem("Test", 0, marker, lines=lines)
        assert len(item2.lines) == 1
        
        # Should reject non-list
        with pytest.raises(TypeError, match="lines must be a list"):
            ListItem("Test", 0, marker, lines="not a list")
        
        # Should reject list with non-Line objects
        with pytest.raises(TypeError, match="All items in lines must be Line"):
            ListItem("Test", 0, marker, lines=["not a Line"])


class TestListItemImmutability:
    """Test cases for ListItem immutability."""

    def test_cannot_modify_content(self):
        """Test that content cannot be modified after creation."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item = ListItem("Original", 0, marker)
        
        with pytest.raises(AttributeError):
            item.content = "Modified"

    def test_cannot_modify_level(self):
        """Test that level cannot be modified after creation."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item = ListItem("Test", 0, marker)
        
        with pytest.raises(AttributeError):
            item.level = 1

    def test_cannot_modify_marker(self):
        """Test that marker cannot be modified after creation."""
        marker1 = ListMarker(ListType.UNORDERED, "-", "", " ")
        marker2 = ListMarker(ListType.UNORDERED, "*", "", " ")
        item = ListItem("Test", 0, marker1)
        
        with pytest.raises(AttributeError):
            item.marker = marker2

    def test_cannot_modify_lines(self):
        """Test that lines cannot be modified after creation."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        lines = [Line("Test", 100.0, 50.0, 12.0)]
        item = ListItem("Test", 0, marker, lines=lines)
        
        # Verify immutability by trying to modify the list
        with pytest.raises(AttributeError):
            item.lines = []


class TestListItemComparison:
    """Test cases for ListItem comparison and equality."""

    def test_equal_list_items(self):
        """Test that identical list items are equal."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item1 = ListItem("Same content", 0, marker)
        item2 = ListItem("Same content", 0, marker)
        
        assert item1 == item2

    def test_unequal_content(self):
        """Test that items with different content are not equal."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item1 = ListItem("Content 1", 0, marker)
        item2 = ListItem("Content 2", 0, marker)
        
        assert item1 != item2

    def test_unequal_level(self):
        """Test that items with different levels are not equal."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item1 = ListItem("Same content", 0, marker)
        item2 = ListItem("Same content", 1, marker)
        
        assert item1 != item2

    def test_unequal_marker(self):
        """Test that items with different markers are not equal."""
        marker1 = ListMarker(ListType.UNORDERED, "-", "", " ")
        marker2 = ListMarker(ListType.UNORDERED, "*", "", " ")
        item1 = ListItem("Same content", 0, marker1)
        item2 = ListItem("Same content", 0, marker2)
        
        assert item1 != item2


class TestListItemMethods:
    """Test cases for ListItem methods."""

    def test_get_indented_content(self):
        """Test getting content with proper indentation."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        
        # Level 0 - no indentation
        item0 = ListItem("Level 0 content", 0, marker)
        assert item0.get_indented_content() == "Level 0 content"
        
        # Level 1 - 2 spaces
        item1 = ListItem("Level 1 content", 1, marker)
        assert item1.get_indented_content() == "  Level 1 content"
        
        # Level 2 - 4 spaces
        item2 = ListItem("Level 2 content", 2, marker)
        assert item2.get_indented_content() == "    Level 2 content"
        
        # Level 3 - 6 spaces
        item3 = ListItem("Level 3 content", 3, marker)
        assert item3.get_indented_content() == "      Level 3 content"

    def test_get_markdown_representation(self):
        """Test getting markdown representation of list item."""
        # Unordered list item
        marker1 = ListMarker(ListType.UNORDERED, "-", "", " ")
        item1 = ListItem("Unordered item", 0, marker1)
        assert item1.to_markdown() == "- Unordered item"
        
        # Nested unordered item
        item2 = ListItem("Nested unordered", 1, marker1)
        assert item2.to_markdown() == "  - Nested unordered"
        
        # Ordered list item
        marker2 = ListMarker(ListType.ORDERED, "1", "", ". ")
        item3 = ListItem("Ordered item", 0, marker2)
        assert item3.to_markdown() == "1. Ordered item"
        
        # Nested ordered item
        marker3 = ListMarker(ListType.ORDERED, "a", "", ". ")
        item4 = ListItem("Nested ordered", 1, marker3)
        assert item4.to_markdown() == "  a. Nested ordered"

    def test_has_continuation(self):
        """Test checking if item has continuation lines."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        
        # Item without lines
        item1 = ListItem("Simple item", 0, marker)
        assert not item1.has_continuation()
        
        # Item with single line
        lines1 = [Line("- Single line", 100.0, 50.0, 12.0)]
        item2 = ListItem("Single line", 0, marker, lines=lines1)
        assert not item2.has_continuation()
        
        # Item with multiple lines
        lines2 = [
            Line("- First line", 100.0, 50.0, 12.0),
            Line("  continuation", 85.0, 50.0, 12.0)
        ]
        item3 = ListItem("First line continuation", 0, marker, lines=lines2)
        assert item3.has_continuation()