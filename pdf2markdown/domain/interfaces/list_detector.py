"""Interface for list detection services."""

from abc import ABC
from abc import abstractmethod
from typing import List
from typing import Optional

from pdf2markdown.domain.models.document import Line
from pdf2markdown.domain.models.document import ListBlock
from pdf2markdown.domain.models.document import ListItem
from pdf2markdown.domain.models.document import ListMarker


class ListDetectorInterface(ABC):
    """Interface for list detection services following Interface Segregation Principle."""

    @abstractmethod
    def detect_list_marker(self, line: Line) -> Optional[ListMarker]:
        """
        Detect list marker in a line of text.
        
        Args:
            line: Line object to analyze
            
        Returns:
            ListMarker if detected, None otherwise
        """
        pass

    @abstractmethod
    def detect_list_items_from_lines(self, lines: List[Line]) -> List[ListItem]:
        """
        Detect list items from a collection of lines.
        
        Args:
            lines: List of Line objects to analyze
            
        Returns:
            List of detected ListItem objects
        """
        pass

    @abstractmethod
    def group_list_items_into_blocks(self, list_items: List[ListItem]) -> List[ListBlock]:
        """
        Group list items into cohesive list blocks.
        
        Args:
            list_items: List of ListItem objects to group
            
        Returns:
            List of ListBlock objects
        """
        pass

    @abstractmethod
    def is_list_marker_line(self, line: Line) -> bool:
        """
        Check if a line contains a list marker.
        
        Args:
            line: Line to check
            
        Returns:
            True if line contains a list marker
        """
        pass
