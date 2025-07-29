"""List detection service implementing pattern recognition and hierarchy analysis."""

import re
from typing import List
from typing import Optional
from typing import Pattern

from pdf2markdown.domain.interfaces.list_detector import ListDetectorInterface
from pdf2markdown.domain.models.document import Line
from pdf2markdown.domain.models.document import ListBlock
from pdf2markdown.domain.models.document import ListItem
from pdf2markdown.domain.models.document import ListMarker
from pdf2markdown.domain.models.document import ListType


class ListDetector(ListDetectorInterface):
    """
    Service for detecting list structures and patterns in text.
    
    Follows:
    - Single Responsibility Principle: Focused on list detection logic
    - Strategy Pattern: Configurable pattern matching strategies
    - Open/Closed Principle: Extensible for new list patterns
    """

    def __init__(
        self,
        indentation_threshold: float = 5.0,
        continuation_indent_threshold: float = 3.0,
        max_nesting_level: int = 3
    ):
        """
        Initialize list detector with configuration.
        
        Args:
            indentation_threshold: Minimum x-position difference to detect indentation
            continuation_indent_threshold: Threshold for continuation line detection
            max_nesting_level: Maximum supported nesting level (0-3)
        """
        self.indentation_threshold = indentation_threshold
        self.continuation_indent_threshold = continuation_indent_threshold
        self.max_nesting_level = max_nesting_level

        # Compile patterns for performance
        self._bullet_patterns = self._compile_bullet_patterns()
        self._ordered_patterns = self._compile_ordered_patterns()

    def _compile_bullet_patterns(self) -> List[Pattern]:
        """Compile regex patterns for bullet point detection."""
        bullet_markers = [
            r'•', r'◦', r'▪', r'▫', r'■', r'□', r'○', r'●',  # Unicode bullets
            r'-', r'\*', r'\+'  # ASCII bullets (escaped for regex)
        ]

        patterns = []
        for marker in bullet_markers:
            # Pattern: optional whitespace + marker + required space + optional content
            # This allows for empty content after marker (like "• ")
            pattern = rf'^(\s*)({marker})\s+(.*)$'
            patterns.append(re.compile(pattern))

        return patterns

    def _compile_ordered_patterns(self) -> List[Pattern]:
        """Compile regex patterns for ordered list detection."""
        patterns = []

        # Numeric patterns: 1. 2. 10. etc.
        patterns.append(re.compile(r'^(\s*)(\d+)(\.|\))\s+(.*)$'))

        # Alphabetic patterns: a. b. A. B. etc.
        patterns.append(re.compile(r'^(\s*)([a-zA-Z])(\.|\))\s+(.*)$'))

        # Roman numeral patterns: i. ii. I. II. etc.
        roman_lower = r'(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)'
        roman_upper = r'(?:I|II|III|IV|V|VI|VII|VIII|IX|X)'
        patterns.append(re.compile(rf'^(\s*)({roman_lower}|{roman_upper})(\.|\))\s+(.*)$'))

        # Parenthetical patterns: (1) (a) (i) etc.
        patterns.append(re.compile(r'^(\s*)\((\d+|[a-zA-Z]|(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)|(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)\s+(.*)$'))

        return patterns

    def detect_list_marker(self, line: Line) -> Optional[ListMarker]:
        """
        Detect list marker in a line of text.
        
        Args:
            line: Line object to analyze
            
        Returns:
            ListMarker if detected, None otherwise
        """
        text = line.text  # Keep original text with trailing spaces for pattern matching

        if not text.strip():
            return None

        # Try bullet patterns first
        for pattern in self._bullet_patterns:
            match = pattern.match(text)
            if match:
                indent_str, marker_symbol, content = match.groups()
                return ListMarker(
                    marker_type=ListType.UNORDERED,
                    symbol=marker_symbol,
                    prefix="",
                    suffix=" "
                )

        # Try ordered patterns
        for pattern in self._ordered_patterns:
            match = pattern.match(text)
            if match:
                groups = match.groups()
                if len(groups) == 4:  # Standard format: indent, symbol, suffix, content
                    indent_str, marker_symbol, suffix_char, content = groups
                    suffix = f"{suffix_char} "
                    prefix = ""
                elif len(groups) == 3:  # Parenthetical format: indent, symbol, content
                    indent_str, marker_symbol, content = groups
                    suffix = ") "
                    prefix = "("
                else:
                    continue

                return ListMarker(
                    marker_type=ListType.ORDERED,
                    symbol=marker_symbol,
                    prefix=prefix,
                    suffix=suffix
                )

        return None

    def detect_list_items_from_lines(self, lines: List[Line]) -> List[ListItem]:
        """
        Detect list items from a collection of lines.
        
        Args:
            lines: List of Line objects to analyze
            
        Returns:
            List of detected ListItem objects
        """
        if not lines:
            return []

        list_items = []
        current_item = None
        base_x_position = None  # Track base indentation level

        for line in lines:
            marker = self.detect_list_marker(line)

            if marker:
                # Save any current item before starting new one
                if current_item:
                    list_items.append(current_item)

                # Determine nesting level based on x-position
                level = self._calculate_nesting_level(line, base_x_position)
                if base_x_position is None:
                    base_x_position = line.x_position

                # Extract content (remove marker from text)
                content = self._extract_content_from_line(line, marker)

                # Handle empty content
                if not content.strip():
                    content = "[empty]"  # Placeholder for empty list items

                # Create list item
                current_item = ListItem(
                    content=content,
                    level=min(level, self.max_nesting_level),
                    marker=marker,
                    lines=[line]
                )
            # Check if this is a continuation line
            elif current_item and self._is_continuation_line(line, current_item):
                # Append to current item's content
                continuation_content = line.text.strip()
                if continuation_content:
                    current_item = ListItem(
                        content=f"{current_item.content} {continuation_content}",
                        level=current_item.level,
                        marker=current_item.marker,
                        lines=current_item.lines + [line]
                    )
            # Non-continuation line - save current item if exists
            elif current_item:
                list_items.append(current_item)
                current_item = None

        # Don't forget the last item
        if current_item:
            list_items.append(current_item)

        return list_items

    def group_list_items_into_blocks(self, list_items: List[ListItem]) -> List[ListBlock]:
        """
        Group list items into cohesive list blocks.
        
        Args:
            list_items: List of ListItem objects to group
            
        Returns:
            List of ListBlock objects
        """
        if not list_items:
            return []

        blocks = []
        current_block = None

        for item in list_items:
            # Check if we need to start a new block
            if (current_block is None or
                current_block.list_type != item.marker.marker_type or
                self._should_start_new_block(current_block, item)):

                # Save current block if exists
                if current_block and not current_block.is_empty():
                    blocks.append(current_block)

                # Start new block
                current_block = ListBlock(list_type=item.marker.marker_type)

            # Add item to current block
            current_block.add_item(item)

        # Don't forget the last block
        if current_block and not current_block.is_empty():
            blocks.append(current_block)

        return blocks

    def is_list_marker_line(self, line: Line) -> bool:
        """
        Check if a line contains a list marker.
        
        Args:
            line: Line to check
            
        Returns:
            True if line contains a list marker
        """
        return self.detect_list_marker(line) is not None

    def _calculate_nesting_level(self, line: Line, base_x_position: Optional[float]) -> int:
        """Calculate nesting level based on x-position indentation."""
        if base_x_position is None:
            return 0

        x_diff = line.x_position - base_x_position

        # Each indentation level represents roughly 10-15 points of x-position difference
        # We'll use 10 points as the threshold per level
        if x_diff < self.indentation_threshold:
            return 0
        elif x_diff < self.indentation_threshold * 2.5:  # More generous for level 1
            return 1
        elif x_diff < self.indentation_threshold * 4:    # More generous for level 2
            return 2
        else:
            return 3  # Maximum nesting level

    def _extract_content_from_line(self, line: Line, marker: ListMarker) -> str:
        """Extract content from line, removing the list marker."""
        text = line.text.strip()

        # Use regex to extract content after marker
        marker_pattern = re.escape(marker.as_string().strip())

        # Try to find and remove the marker from the beginning
        pattern = rf'^(\s*){re.escape(marker.prefix)}{re.escape(marker.symbol)}{re.escape(marker.suffix.rstrip())}\s*(.*)'
        match = re.match(pattern, text)

        if match:
            return match.groups()[-1].strip()  # Return the content part
        else:
            # Fallback: remove marker manually
            marker_str = marker.as_string()
            if text.startswith(marker_str):
                return text[len(marker_str):].strip()
            else:
                # Last resort: find first word that matches marker and remove it
                words = text.split()
                if words and words[0] == marker.symbol + marker.suffix.rstrip():
                    return " ".join(words[1:])
                return text.strip()

    def _is_continuation_line(self, line: Line, current_item: ListItem) -> bool:
        """Check if a line is a continuation of the current list item."""
        if not current_item or not current_item.lines:
            return False

        # Get the x-position of the current item's first line
        first_line = current_item.lines[0]
        marker = self.detect_list_marker(first_line)

        if not marker:
            return False

        # Calculate expected indentation for continuation
        marker_length = len(marker.as_string())
        expected_x_position = first_line.x_position + (marker_length * 2)  # Approximate character width

        # Check if line is indented appropriately for continuation
        x_diff = abs(line.x_position - expected_x_position)

        # Line should be indented more than the marker but not too much
        return (line.x_position > first_line.x_position and
                x_diff <= self.continuation_indent_threshold * 3)

    def _should_start_new_block(self, current_block: ListBlock, item: ListItem) -> bool:
        """Determine if a new block should be started for the given item."""
        if not current_block or current_block.is_empty():
            return True

        # Different list types should be in different blocks
        if current_block.list_type != item.marker.marker_type:
            return True

        # Check for significant gap in nesting levels or ordering
        last_item = current_block.items[-1] if current_block.items else None
        if last_item:
            # If there's a large gap in nesting levels, might be a separate list
            level_gap = abs(item.level - last_item.level)
            if level_gap > 2:
                return True

        return False
