"""Domain models for document structure following Clean Architecture principles."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional


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

    def __post_init__(self):
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
                markdown_parts.append(markdown_content)
                if isinstance(block, Heading):
                    markdown_parts.append("")  # Empty line after headings

        return "\n".join(markdown_parts).strip()
