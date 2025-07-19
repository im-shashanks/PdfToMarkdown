"""
PdfToMarkdown - Convert PDF documents to Markdown format.

A lightweight, enterprise-grade CLI tool for converting PDF documents
to clean, structured Markdown format with support for tables, headings,
and text formatting.
"""

__version__ = "1.0.0"
__author__ = "PdfToMarkdown Development Team"
__email__ = "dev@pdf2markdown.com"
__description__ = "Convert PDF documents to Markdown format"

# Package-level imports for convenience
from pdf2markdown.core.exceptions import InvalidPdfError
from pdf2markdown.core.exceptions import PdfToMarkdownError
from pdf2markdown.core.exceptions import ProcessingError

__all__ = [
    "InvalidPdfError",
    "PdfToMarkdownError",
    "ProcessingError",
    "__author__",
    "__description__",
    "__email__",
    "__version__",
]
