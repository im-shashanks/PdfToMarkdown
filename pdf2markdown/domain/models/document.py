"""Domain models for document structure following Clean Architecture principles."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional


class TextAlignment(Enum):
    """Text alignment options for paragraphs."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class ListType(Enum):
    """Types of lists supported."""
    ORDERED = "ordered"
    UNORDERED = "unordered"


@dataclass(frozen=True)
class ListMarker:
    """
    Value object representing a list marker.
    
    Immutable by design to ensure data integrity.
    """
    marker_type: ListType
    symbol: str  # The actual marker symbol (e.g., "•", "1", "a")
    prefix: str = ""  # Prefix like "(" in "(a)"
    suffix: str = " "  # Suffix like ". " in "1. " or ") " in "(a) "
    
    def as_string(self) -> str:
        """Get the full marker string representation."""
        return f"{self.prefix}{self.symbol}{self.suffix}"


@dataclass(frozen=True)
class Line:
    """
    Value object representing a line of text with positioning information.
    
    Immutable by design to ensure data integrity.
    """
    text: str
    y_position: float  # Vertical position (top of line)
    x_position: float  # Horizontal position (start of line)
    height: float      # Line height
    font_size: Optional[float] = None

    def vertical_spacing_to(self, other: "Line") -> float:
        """Calculate vertical spacing to another line."""
        return self.y_position - other.y_position - other.height

    def is_aligned_with(self, other: "Line", tolerance: float = 5.0) -> bool:
        """Check if horizontally aligned with another line."""
        return abs(self.x_position - other.x_position) <= tolerance


@dataclass(frozen=True)
class TextFlow:
    """
    Value object containing text flow metadata.
    
    Immutable to maintain consistency across paragraph analysis.
    """
    alignment: TextAlignment = TextAlignment.LEFT
    line_spacing: float = 1.0  # Multiplier of average line height
    indentation: float = 0.0   # Indentation in points
    average_line_height: float = 12.0

    def is_similar_to(self, other: "TextFlow", spacing_tolerance: float = 0.1) -> bool:
        """Check if text flow is similar to another."""
        return (self.alignment == other.alignment and
                abs(self.line_spacing - other.line_spacing) <= spacing_tolerance)


@dataclass(frozen=True)
class ListItem:
    """
    Value object representing a single list item.
    
    Immutable to maintain consistency across list processing.
    """
    content: str
    level: int  # Nesting level (0-3)
    marker: ListMarker
    lines: List[Line] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate list item constraints."""
        if self.level < 0:
            raise ValueError("List item level must be non-negative")
        if self.level > 3:
            raise ValueError("List item level cannot exceed 3")
        if not self.content.strip():
            raise ValueError("List item content cannot be empty")
        if not isinstance(self.marker, ListMarker):
            raise TypeError("marker must be a ListMarker instance")
        if not isinstance(self.lines, list):
            raise TypeError("lines must be a list")
        if any(not isinstance(line, Line) for line in self.lines):
            raise TypeError("All items in lines must be Line instances")
    
    def get_indented_content(self) -> str:
        """Get content with proper indentation based on level."""
        indent = "  " * self.level  # 2 spaces per level
        return f"{indent}{self.content}"
    
    def to_markdown(self) -> str:
        """Convert list item to markdown format."""
        indent = "  " * self.level
        if self.marker.marker_type == ListType.UNORDERED:
            return f"{indent}- {self.content}"
        else:
            # For ordered lists, preserve the original marker
            return f"{indent}{self.marker.as_string()}{self.content}"
    
    def has_continuation(self) -> bool:
        """Check if this item has continuation lines."""
        return len(self.lines) > 1


@dataclass
class Block(ABC):
    """Abstract base class for document elements following Interface Segregation Principle."""

    @abstractmethod
    def to_markdown(self) -> str:
        """Convert block to markdown representation."""
        pass


@dataclass
class Heading(Block):
    """
    Represents a heading in the document.
    
    Follows Single Responsibility Principle - only responsible for heading data.
    """
    level: int  # 1-6 for H1-H6
    content: str
    font_size: Optional[float] = None
    is_bold: bool = False

    def __post_init__(self) -> None:
        """Validate heading level constraints."""
        if not 1 <= self.level <= 6:
            raise ValueError(f"Heading level must be between 1 and 6, got {self.level}")
        if not self.content.strip():
            raise ValueError("Heading content cannot be empty")

    def to_markdown(self) -> str:
        """Convert heading to markdown format."""
        return f"{'#' * self.level} {self.content.strip()}"


@dataclass
class TextBlock(Block):
    """
    Represents a regular text block.
    
    Supports future extension for paragraphs, lists, etc.
    """
    content: str
    font_size: Optional[float] = None

    def to_markdown(self) -> str:
        """Convert text block to markdown format."""
        return self.content.strip()


@dataclass
class Paragraph(Block):
    """
    Represents a paragraph with proper formatting and text flow analysis.
    
    Follows Single Responsibility Principle - handles paragraph structure and formatting.
    """
    lines: List[Line] = field(default_factory=list)
    text_flow: Optional[TextFlow] = None
    font_size: Optional[float] = None
    is_continuation: bool = False
    preserve_line_breaks: bool = False

    @property
    def content(self) -> str:
        """Get concatenated text content from all lines."""
        return " ".join(line.text for line in self.lines)

    def add_line(self, line: Line) -> None:
        """Add a line to the paragraph."""
        if not isinstance(line, Line):
            raise TypeError(f"Expected Line instance, got {type(line)}")
        self.lines.append(line)

    def merge_with(self, other: "Paragraph") -> None:
        """Merge another paragraph into this one."""
        if not isinstance(other, Paragraph):
            raise TypeError(f"Expected Paragraph instance, got {type(other)}")
        self.lines.extend(other.lines)

    def is_empty(self) -> bool:
        """Check if paragraph has no meaningful content."""
        return not any(line.text.strip() for line in self.lines)

    def get_bounding_box(self) -> Dict[str, float]:
        """Calculate bounding box of the paragraph."""
        if not self.lines:
            return {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0}

        y_positions = [line.y_position for line in self.lines]
        x_positions = [line.x_position for line in self.lines]

        return {
            "top": max(y_positions),
            "bottom": min(y_positions),
            "left": min(x_positions),
            "right": max(x_positions)  # Simplified - actual text width calculation needed
        }

    def to_markdown(self) -> str:
        """Convert paragraph to markdown format with proper spacing."""
        if self.is_empty():
            return ""

        if self.preserve_line_breaks:
            # Hard line breaks with double space
            lines_text = []
            for i, line in enumerate(self.lines):
                text = line.text.strip()
                if text:
                    if i < len(self.lines) - 1:  # Not the last line
                        lines_text.append(f"{text}  ")  # Two spaces for line break
                    else:
                        lines_text.append(text)
            return "\n".join(lines_text) + "\n"
        else:
            # Soft line breaks - join with spaces
            content = self.content.strip()

            # Preserve meaningful indentation
            if self.text_flow and self.text_flow.indentation > 5.0:
                # Significant indentation detected
                indent_spaces = "    "  # 4 spaces for indentation
                return f"{indent_spaces}{content}\n"
            else:
                return f"{content}\n"


@dataclass
class ListBlock(Block):
    """
    Represents a list structure in the document.
    
    Follows Single Responsibility Principle - only responsible for list data.
    """
    list_type: ListType
    items: List[ListItem] = field(default_factory=list)
    nested_lists: Dict[int, 'ListBlock'] = field(default_factory=dict)  # For mixed list types
    
    def add_item(self, item: ListItem) -> None:
        """Add an item to the list with validation."""
        if not isinstance(item, ListItem):
            raise TypeError(f"Expected ListItem instance, got {type(item)}")
        
        # Validate that item type matches list type (for non-nested items)
        if item.level == 0 and item.marker.marker_type != self.list_type:
            raise ValueError(f"List type mismatch: expected {self.list_type.value}, got {item.marker.marker_type.value}")
        
        self.items.append(item)
    
    def add_nested_list(self, nested_list: 'ListBlock', parent_index: int) -> None:
        """Add a nested list of different type."""
        if not isinstance(nested_list, ListBlock):
            raise TypeError(f"Expected ListBlock instance, got {type(nested_list)}")
        self.nested_lists[parent_index] = nested_list
    
    def is_empty(self) -> bool:
        """Check if list has no items."""
        return len(self.items) == 0
    
    def get_max_level(self) -> int:
        """Get the maximum nesting level in the list."""
        if not self.items:
            return -1
        return max(item.level for item in self.items)
    
    def to_markdown(self) -> str:
        """Convert list to markdown format."""
        if self.is_empty():
            return ""
        
        lines = []
        for i, item in enumerate(self.items):
            # Check if this item has a nested list of different type
            if i in self.nested_lists:
                lines.append(self._format_item_markdown(item))
                # Add nested list with proper indentation
                nested = self.nested_lists[i]
                nested_markdown = nested.to_markdown()
                if nested_markdown:
                    # Indent nested list by 3 spaces under ordered items
                    indent = "   "
                    nested_lines = nested_markdown.split('\n')
                    indented_lines = [indent + line for line in nested_lines]
                    lines.extend(indented_lines)
            else:
                lines.append(self._format_item_markdown(item))
        
        return '\n'.join(lines)
    
    def _format_item_markdown(self, item: ListItem) -> str:
        """Format a single item to markdown."""
        indent = "  " * item.level
        if self.list_type == ListType.UNORDERED:
            return f"{indent}- {item.content}"
        else:
            # For ordered lists, use sequential numbering
            return f"{indent}{self._get_item_number(item)}. {item.content}"
    
    def _get_item_number(self, target_item: ListItem) -> str:
        """Get the appropriate number for an ordered list item."""
        # Count items at the same level that come before this item
        count = 1
        for item in self.items:
            if item == target_item:
                break
            if item.level == target_item.level:
                count += 1
        return str(count)


@dataclass
class Document:
    """
    Root document entity representing the entire PDF document.
    
    Follows Dependency Inversion Principle - depends on Block abstraction.
    """
    title: Optional[str] = None
    blocks: List[Block] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_block(self, block: Block) -> None:
        """Add a block to the document."""
        if not isinstance(block, Block):
            raise TypeError(f"Expected Block instance, got {type(block)}")
        self.blocks.append(block)

    def to_markdown(self) -> str:
        """Convert entire document to markdown."""
        markdown_parts = []

        if self.title:
            markdown_parts.append(f"# {self.title}")
            markdown_parts.append("")  # Empty line after title

        for block in self.blocks:
            markdown_content = block.to_markdown()
            if markdown_content:
                # Remove trailing newline for joining, but preserve content formatting
                content = markdown_content.rstrip('\n')
                if content.strip():  # Check for actual content, not whitespace-only
                    markdown_parts.append(content)
                    if isinstance(block, Heading):
                        markdown_parts.append("")  # Empty line after headings

        return "\n".join(markdown_parts).rstrip()
