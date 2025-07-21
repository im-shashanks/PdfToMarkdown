"""Unit tests for ListBlock domain model."""

import pytest

from pdf2markdown.domain.models.document import Block
from pdf2markdown.domain.models.document import Line
from pdf2markdown.domain.models.document import ListBlock
from pdf2markdown.domain.models.document import ListItem
from pdf2markdown.domain.models.document import ListMarker
from pdf2markdown.domain.models.document import ListType


class TestListType:
    """Test cases for ListType enum."""

    def test_list_type_values(self):
        """Test that ListType enum has expected values."""
        assert ListType.ORDERED.value == "ordered"
        assert ListType.UNORDERED.value == "unordered"

    def test_list_type_members(self):
        """Test that all expected list types are present."""
        assert hasattr(ListType, "ORDERED")
        assert hasattr(ListType, "UNORDERED")


class TestListMarker:
    """Test cases for ListMarker value object."""

    def test_create_unordered_marker(self):
        """Test creating an unordered list marker."""
        marker = ListMarker(
            marker_type=ListType.UNORDERED,
            symbol="•",
            prefix="",
            suffix=" "
        )
        assert marker.marker_type == ListType.UNORDERED
        assert marker.symbol == "•"
        assert marker.prefix == ""
        assert marker.suffix == " "

    def test_create_ordered_marker(self):
        """Test creating an ordered list marker."""
        marker = ListMarker(
            marker_type=ListType.ORDERED,
            symbol="1",
            prefix="",
            suffix=". "
        )
        assert marker.marker_type == ListType.ORDERED
        assert marker.symbol == "1"
        assert marker.prefix == ""
        assert marker.suffix == ". "

    def test_marker_with_parentheses(self):
        """Test creating a marker with parentheses."""
        marker = ListMarker(
            marker_type=ListType.ORDERED,
            symbol="a",
            prefix="(",
            suffix=") "
        )
        assert marker.prefix == "("
        assert marker.symbol == "a"
        assert marker.suffix == ") "

    def test_marker_immutability(self):
        """Test that ListMarker is immutable."""
        marker = ListMarker(
            marker_type=ListType.UNORDERED,
            symbol="-",
            prefix="",
            suffix=" "
        )
        with pytest.raises(AttributeError):
            marker.symbol = "*"

    def test_marker_string_representation(self):
        """Test string representation of marker."""
        marker = ListMarker(
            marker_type=ListType.ORDERED,
            symbol="1",
            prefix="",
            suffix=". "
        )
        assert marker.as_string() == "1. "

    def test_marker_string_with_prefix(self):
        """Test string representation with prefix."""
        marker = ListMarker(
            marker_type=ListType.ORDERED,
            symbol="a",
            prefix="(",
            suffix=") "
        )
        assert marker.as_string() == "(a) "


class TestListItem:
    """Test cases for ListItem value object."""

    def test_create_simple_list_item(self):
        """Test creating a simple list item."""
        marker = ListMarker(ListType.UNORDERED, "•", "", " ")
        item = ListItem(
            content="Test item",
            level=0,
            marker=marker
        )
        assert item.content == "Test item"
        assert item.level == 0
        assert item.marker == marker

    def test_create_nested_list_item(self):
        """Test creating a nested list item."""
        marker = ListMarker(ListType.UNORDERED, "◦", "", " ")
        item = ListItem(
            content="Nested item",
            level=1,
            marker=marker
        )
        assert item.level == 1

    def test_list_item_with_lines(self):
        """Test list item with line information."""
        marker = ListMarker(ListType.ORDERED, "1", "", ". ")
        lines = [
            Line("1. First line", 100.0, 50.0, 12.0),
            Line("   continuation", 85.0, 50.0, 12.0)
        ]
        item = ListItem(
            content="First line continuation",
            level=0,
            marker=marker,
            lines=lines
        )
        assert len(item.lines) == 2
        assert item.lines[0].text == "1. First line"

    def test_list_item_immutability(self):
        """Test that ListItem is immutable."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item = ListItem(
            content="Test",
            level=0,
            marker=marker
        )
        with pytest.raises(AttributeError):
            item.content = "Modified"

    def test_list_item_level_validation(self):
        """Test that list item level must be non-negative."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        with pytest.raises(ValueError, match="level must be non-negative"):
            ListItem(
                content="Test",
                level=-1,
                marker=marker
            )

    def test_list_item_max_level_validation(self):
        """Test that list item level has maximum limit."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        with pytest.raises(ValueError, match="level cannot exceed"):
            ListItem(
                content="Test",
                level=4,  # Max is 3
                marker=marker
            )

    def test_list_item_empty_content_validation(self):
        """Test that list item content cannot be empty."""
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        with pytest.raises(ValueError, match="content cannot be empty"):
            ListItem(
                content="",
                level=0,
                marker=marker
            )


class TestListBlock:
    """Test cases for ListBlock domain model."""

    def test_list_block_inheritance(self):
        """Test that ListBlock inherits from Block."""
        assert issubclass(ListBlock, Block)

    def test_create_empty_list_block(self):
        """Test creating an empty list block."""
        list_block = ListBlock(list_type=ListType.UNORDERED)
        assert list_block.list_type == ListType.UNORDERED
        assert list_block.items == []

    def test_add_item_to_list_block(self):
        """Test adding items to list block."""
        list_block = ListBlock(list_type=ListType.ORDERED)
        
        marker1 = ListMarker(ListType.ORDERED, "1", "", ". ")
        item1 = ListItem("First item", 0, marker1)
        list_block.add_item(item1)
        
        marker2 = ListMarker(ListType.ORDERED, "2", "", ". ")
        item2 = ListItem("Second item", 0, marker2)
        list_block.add_item(item2)
        
        assert len(list_block.items) == 2
        assert list_block.items[0].content == "First item"
        assert list_block.items[1].content == "Second item"

    def test_add_nested_items(self):
        """Test adding nested items to list block."""
        list_block = ListBlock(list_type=ListType.UNORDERED)
        
        marker1 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item1 = ListItem("Parent item", 0, marker1)
        list_block.add_item(item1)
        
        marker2 = ListMarker(ListType.UNORDERED, "◦", "", " ")
        item2 = ListItem("Child item", 1, marker2)
        list_block.add_item(item2)
        
        marker3 = ListMarker(ListType.UNORDERED, "▪", "", " ")
        item3 = ListItem("Grandchild item", 2, marker3)
        list_block.add_item(item3)
        
        assert len(list_block.items) == 3
        assert list_block.items[0].level == 0
        assert list_block.items[1].level == 1
        assert list_block.items[2].level == 2

    def test_mixed_type_validation(self):
        """Test that adding wrong type items is rejected."""
        list_block = ListBlock(list_type=ListType.ORDERED)
        
        # Should accept ordered marker
        marker1 = ListMarker(ListType.ORDERED, "1", "", ". ")
        item1 = ListItem("First", 0, marker1)
        list_block.add_item(item1)
        
        # Should reject unordered marker in ordered list
        marker2 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item2 = ListItem("Second", 0, marker2)
        with pytest.raises(ValueError, match="type mismatch"):
            list_block.add_item(item2)

    def test_to_markdown_unordered_list(self):
        """Test converting unordered list to markdown."""
        list_block = ListBlock(list_type=ListType.UNORDERED)
        
        marker1 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item1 = ListItem("First item", 0, marker1)
        list_block.add_item(item1)
        
        marker2 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item2 = ListItem("Second item", 0, marker2)
        list_block.add_item(item2)
        
        markdown = list_block.to_markdown()
        expected = "- First item\n- Second item"
        assert markdown == expected

    def test_to_markdown_ordered_list(self):
        """Test converting ordered list to markdown."""
        list_block = ListBlock(list_type=ListType.ORDERED)
        
        marker1 = ListMarker(ListType.ORDERED, "1", "", ". ")
        item1 = ListItem("First item", 0, marker1)
        list_block.add_item(item1)
        
        marker2 = ListMarker(ListType.ORDERED, "2", "", ". ")
        item2 = ListItem("Second item", 0, marker2)
        list_block.add_item(item2)
        
        markdown = list_block.to_markdown()
        expected = "1. First item\n2. Second item"
        assert markdown == expected

    def test_to_markdown_nested_list(self):
        """Test converting nested list to markdown."""
        list_block = ListBlock(list_type=ListType.UNORDERED)
        
        marker1 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item1 = ListItem("Parent item", 0, marker1)
        list_block.add_item(item1)
        
        marker2 = ListMarker(ListType.UNORDERED, "◦", "", " ")
        item2 = ListItem("Child item", 1, marker2)
        list_block.add_item(item2)
        
        marker3 = ListMarker(ListType.UNORDERED, "▪", "", " ")
        item3 = ListItem("Grandchild item", 2, marker3)
        list_block.add_item(item3)
        
        markdown = list_block.to_markdown()
        expected = "- Parent item\n  - Child item\n    - Grandchild item"
        assert markdown == expected

    def test_to_markdown_mixed_nested_lists(self):
        """Test converting mixed nested lists to markdown."""
        list_block = ListBlock(list_type=ListType.ORDERED)
        
        marker1 = ListMarker(ListType.ORDERED, "1", "", ". ")
        item1 = ListItem("First item", 0, marker1)
        list_block.add_item(item1)
        
        # Create a sub-list block for nested unordered items
        sub_list = ListBlock(list_type=ListType.UNORDERED)
        list_block.add_nested_list(sub_list, parent_index=0)
        
        marker2 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item2 = ListItem("Nested unordered", 0, marker2)  # Level 0 in sub-list
        sub_list.add_item(item2)
        
        markdown = list_block.to_markdown()
        expected = "1. First item\n   - Nested unordered"
        assert markdown == expected

    def test_is_empty(self):
        """Test is_empty method."""
        list_block = ListBlock(list_type=ListType.UNORDERED)
        assert list_block.is_empty()
        
        marker = ListMarker(ListType.UNORDERED, "-", "", " ")
        item = ListItem("Test", 0, marker)
        list_block.add_item(item)
        assert not list_block.is_empty()

    def test_get_max_level(self):
        """Test getting maximum nesting level."""
        list_block = ListBlock(list_type=ListType.UNORDERED)
        assert list_block.get_max_level() == -1  # Empty list
        
        marker1 = ListMarker(ListType.UNORDERED, "•", "", " ")
        item1 = ListItem("Level 0", 0, marker1)
        list_block.add_item(item1)
        assert list_block.get_max_level() == 0
        
        marker2 = ListMarker(ListType.UNORDERED, "◦", "", " ")
        item2 = ListItem("Level 1", 1, marker2)
        list_block.add_item(item2)
        assert list_block.get_max_level() == 1
        
        marker3 = ListMarker(ListType.UNORDERED, "▪", "", " ")
        item3 = ListItem("Level 2", 2, marker3)
        list_block.add_item(item3)
        assert list_block.get_max_level() == 2

    def test_add_item_type_validation(self):
        """Test that only ListItem instances can be added."""
        list_block = ListBlock(list_type=ListType.UNORDERED)
        
        with pytest.raises(TypeError, match="Expected ListItem"):
            list_block.add_item("Not a list item")