"""Markdown formatter for converting documents to markdown format."""

import logging

from pdf2markdown.domain.interfaces import FormatterInterface
from pdf2markdown.domain.models import Document


class MarkdownFormatter(FormatterInterface):
    """
    Formatter for converting Document objects to markdown format.
    
    Follows:
    - Single Responsibility: Only responsible for markdown formatting
    - Open/Closed: Can be extended for different markdown styles
    - Dependency Inversion: Depends on Document abstraction
    """

    def __init__(self) -> None:
        """Initialize the markdown formatter."""
        self.logger = logging.getLogger(__name__)

    def format_document(self, document: Document) -> str:
        """
        Convert a Document to markdown format.
        
        Args:
            document: Document to convert
            
        Returns:
            str: Markdown representation of the document
        """
        if not document:
            self.logger.warning("Document is None or empty")
            return ""

        # Use the document's built-in to_markdown method
        # This leverages the domain model's knowledge of markdown conversion
        markdown_content = document.to_markdown()

        self.logger.info(f"Formatted document with {len(document.blocks)} blocks to markdown")
        return markdown_content

    def format_to_file(self, document: Document, output_path: str) -> None:
        """
        Convert document to markdown and write to file.
        
        Args:
            document: Document to convert
            output_path: Path to write markdown file
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            markdown_content = self.format_document(document)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            self.logger.info(f"Written markdown to {output_path}")

        except Exception as e:
            self.logger.error(f"Error writing markdown to {output_path}: {e}")
            raise OSError(f"Failed to write markdown file: {e}") from e
