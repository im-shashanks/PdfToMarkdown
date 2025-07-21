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
