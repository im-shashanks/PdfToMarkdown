"""
Main CLI interface for PdfToMarkdown application.

This module provides the primary command-line interface following
clean architecture principles with proper separation of concerns
and comprehensive error handling.
"""

import logging
import sys
from typing import NoReturn
from typing import Optional

from pdf2markdown.cli.argument_parser import CliArguments
from pdf2markdown.cli.argument_parser import create_argument_parser
from pdf2markdown.cli.output_handler import create_output_handler
from pdf2markdown.core.config import ApplicationConfig
from pdf2markdown.core.config import config_manager
from pdf2markdown.core.dependency_injection import DependencyInjectionContainer
from pdf2markdown.core.dependency_injection import create_default_container
from pdf2markdown.core.exceptions import ConfigurationError
from pdf2markdown.core.exceptions import FileSystemError
from pdf2markdown.core.exceptions import InvalidPdfError
from pdf2markdown.core.exceptions import PdfToMarkdownError
from pdf2markdown.core.exceptions import ProcessingError
from pdf2markdown.core.exceptions import ValidationError
from pdf2markdown.core.file_validator import create_file_validator
from pdf2markdown.domain.interfaces import CodeDetectorInterface
from pdf2markdown.domain.interfaces import DocumentAnalyzerInterface
from pdf2markdown.domain.interfaces import FormatterInterface
from pdf2markdown.domain.interfaces import HeadingDetectorInterface
from pdf2markdown.domain.interfaces import LanguageDetectorInterface
from pdf2markdown.domain.interfaces import ListDetectorInterface
from pdf2markdown.domain.interfaces import ParagraphDetectorInterface
from pdf2markdown.domain.interfaces import PdfParserStrategy
from pdf2markdown.domain.models.document import Document


class PdfToMarkdownCli:
    """Main CLI application class.
    
    This class orchestrates the CLI application following clean architecture
    principles, handling user input, coordinating services, and managing
    the application lifecycle.
    """

    def __init__(
        self,
        config: Optional[ApplicationConfig] = None,
        container: Optional[DependencyInjectionContainer] = None
    ) -> None:
        """Initialize CLI application with dependency injection.
        
        Args:
            config: Optional application configuration (uses default if None)
            container: Optional dependency injection container (creates default if None)
        """
        self._config = config or config_manager.get_config()
        self._container = container or create_default_container(self._config)
        self._logger = self._setup_logging()
        self._argument_parser = create_argument_parser(self._config)
        self._file_validator = create_file_validator(self._config)
        self._output_handler = create_output_handler(self._config)

        # Resolve dependencies through dependency injection
        self._pdf_parser = self._container.resolve(PdfParserStrategy)
        self._document_analyzer = self._container.resolve(DocumentAnalyzerInterface)
        self._heading_detector = self._container.resolve(HeadingDetectorInterface)
        self._paragraph_detector = self._container.resolve(ParagraphDetectorInterface)
        self._list_detector = self._container.resolve(ListDetectorInterface)
        self._code_detector = self._container.resolve(CodeDetectorInterface)
        self._language_detector = self._container.resolve(LanguageDetectorInterface)
        self._markdown_formatter = self._container.resolve(FormatterInterface)

    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI application with given arguments.
        
        Args:
            args: Optional command-line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        try:
            # Parse command-line arguments
            cli_args = self._argument_parser.parse_args(args)

            # Configure logging based on CLI arguments
            self._configure_logging_for_args(cli_args)

            # Log startup information
            self._logger.info(f"Starting {self._config.app_name} v{self._config.version}")
            self._logger.debug(f"CLI arguments: {cli_args.to_dict()}")

            # Validate input file
            input_validation = self._file_validator.validate_pdf_file(cli_args.input_file)
            if not input_validation.is_valid:
                self._output_handler.error(f"Invalid input file: {input_validation.get_error_summary()}")
                return 2

            # Show warnings if any
            for warning in input_validation.warnings:
                self._output_handler.warning(warning)

            # Validate output path
            output_validation = self._file_validator.validate_output_path(
                cli_args.output_file,
                cli_args.force
            )
            if not output_validation.is_valid:
                self._output_handler.error(f"Invalid output path: {output_validation.get_error_summary()}")
                return 3

            # Show output warnings if any
            for warning in output_validation.warnings:
                self._output_handler.warning(warning)

            # Process the PDF file
            self._process_pdf_file(cli_args)

            # Success
            if not cli_args.quiet:
                self._output_handler.success(
                    f"Successfully converted {cli_args.input_file} to {cli_args.output_file}"
                )

            return 0

        except SystemExit as e:
            # Handle --help and --version which cause SystemExit
            return int(e.code) if e.code is not None else 0

        except KeyboardInterrupt:
            self._output_handler.error("Operation cancelled by user")
            return 130  # Standard exit code for SIGINT

        except ValidationError as e:
            self._output_handler.error(f"Validation error: {e.message}")
            if self._config.debug:
                self._logger.exception("Validation error details")
            return 2

        except InvalidPdfError as e:
            self._output_handler.error(f"Invalid PDF: {e.message}")
            if self._config.debug:
                self._logger.exception("PDF error details")
            return 4

        except ProcessingError as e:
            self._output_handler.error(f"Processing error: {e.message}")
            if self._config.debug:
                self._logger.exception("Processing error details")
            return 5

        except FileSystemError as e:
            self._output_handler.error(f"File system error: {e.message}")
            if self._config.debug:
                self._logger.exception("File system error details")
            return 6

        except ConfigurationError as e:
            self._output_handler.error(f"Configuration error: {e.message}")
            if self._config.debug:
                self._logger.exception("Configuration error details")
            return 7

        except PdfToMarkdownError as e:
            self._output_handler.error(f"Application error: {e.message}")
            if self._config.debug:
                self._logger.exception("Application error details")
            return 1

        except Exception as e:
            self._output_handler.error(f"Unexpected error: {e}")
            self._logger.exception("Unexpected error occurred")
            return 99

    def _process_pdf_file(self, cli_args: CliArguments) -> None:
        """Process the PDF file and generate Markdown output.
        
        Args:
            cli_args: Validated CLI arguments
            
        Raises:
            ProcessingError: If processing fails
        """
        if not cli_args.quiet:
            self._output_handler.info(f"Processing {cli_args.input_file}...")

        try:
            # Step 1: Parse PDF document
            self._logger.debug("Parsing PDF document...")
            document = self._pdf_parser.parse_document(cli_args.input_file)
            self._logger.info(f"Extracted {len(document.blocks)} text blocks from PDF")

            # Step 2: Analyze document type and characteristics
            self._logger.debug("Analyzing document type...")
            document_analysis = self._document_analyzer.analyze_document_type(document)
            self._logger.info(f"Detected document type: {document_analysis.document_type.value} "
                            f"(confidence: {document_analysis.confidence:.2f})")

            # Get processing recommendations based on document type
            recommendations = self._document_analyzer.get_processing_recommendations(document_analysis)
            self._logger.debug(f"Using processing strategy: {document_analysis.suggested_processing_strategy}")

            # Step 3: Apply adaptive paragraph detection
            self._logger.debug("Detecting paragraphs with adaptive processing...")
            # Configure paragraph detector based on recommendations
            paragraph_config = recommendations.get('paragraph_detection', {})
            self._paragraph_detector.line_spacing_threshold = paragraph_config.get('line_spacing_threshold', 1.8)
            self._paragraph_detector.content_aware_merging = not paragraph_config.get('merge_aggressive', False)

            document_with_paragraphs = self._paragraph_detector.detect_paragraphs_in_document(document)

            # Count paragraphs for logging
            paragraph_count = sum(1 for block in document_with_paragraphs.blocks
                                if hasattr(block, 'lines'))
            self._logger.info(f"Detected {paragraph_count} paragraphs in document")

            # Step 4: Apply list detection
            self._logger.debug("Detecting list structures...")

            # Use the enhanced parser's line extraction for precise list detection
            from pdf2markdown.domain.models.document import Line

            # Extract lines with positioning information
            lines = []
            try:
                for text, x_pos, y_pos, height, page_num in self._pdf_parser.extract_line_elements(cli_args.input_file):
                    lines.append(Line(text, y_pos, x_pos, height))
            except Exception as e:
                self._logger.warning(f"Could not extract line positioning for list detection: {e}")
                # Fallback: continue without list detection
                lines = []

            if lines:
                # Detect list items from positioned lines
                list_items = self._list_detector.detect_list_items_from_lines(lines)
                if list_items:
                    # Group list items into blocks
                    list_blocks = self._list_detector.group_list_items_into_blocks(list_items)

                    # Create a new document with list blocks integrated
                    document_with_lists = Document(
                        title=document_with_paragraphs.title,
                        metadata=document_with_paragraphs.metadata
                    )

                    # Merge list blocks with existing blocks based on positioning
                    self._integrate_list_blocks_into_document(
                        document_with_lists,
                        document_with_paragraphs,
                        list_blocks
                    )

                    list_count = len(list_blocks)
                    item_count = sum(len(block.items) for block in list_blocks)
                    self._logger.info(f"Detected {list_count} lists with {item_count} total items")

                    document_with_paragraphs = document_with_lists
                else:
                    self._logger.debug("No list structures detected")
            else:
                self._logger.debug("Skipping list detection due to line extraction issues")

            # Step 5: Apply code block detection
            self._logger.debug("Detecting code blocks...")

            # Use the same line extraction for code detection
            if lines:
                # Detect code blocks from positioned lines
                code_blocks = self._code_detector.detect_code_blocks(lines)

                if code_blocks:
                    # Apply language detection to each code block
                    for code_block in code_blocks:
                        analyzed_block = self._language_detector.analyze_code_block(code_block)
                        # Update the code block with detected language
                        code_block.language = analyzed_block.language

                    # Create a new document with code blocks integrated
                    document_with_code = Document(
                        title=document_with_paragraphs.title,
                        metadata=document_with_paragraphs.metadata
                    )

                    # Merge code blocks with existing blocks based on positioning
                    self._integrate_code_blocks_into_document(
                        document_with_code,
                        document_with_paragraphs,
                        code_blocks
                    )

                    code_count = len(code_blocks)
                    self._logger.info(f"Detected {code_count} code blocks")

                    document_with_paragraphs = document_with_code
                else:
                    self._logger.debug("No code blocks detected")
            else:
                self._logger.debug("Skipping code detection due to line extraction issues")

            # Step 6: Apply adaptive heading detection
            self._logger.debug("Detecting headings with adaptive processing...")
            # Configure heading detector based on recommendations
            heading_config = recommendations.get('heading_detection', {})
            if hasattr(self._heading_detector, 'config'):
                self._heading_detector.config.min_size_difference = heading_config.get('font_size_threshold', 0.1)
                # Scale pattern weights based on document type
                pattern_weight = heading_config.get('pattern_weight', 1.0)
                caps_weight = heading_config.get('caps_weight', 1.0)

            document_with_headings = self._heading_detector.detect_headings_in_document(document_with_paragraphs)

            # Count headings for logging
            heading_count = sum(1 for block in document_with_headings.blocks
                              if hasattr(block, 'level'))
            self._logger.info(f"Detected {heading_count} headings in document")

            # Log document analysis results for debugging
            if self._config.debug:
                self._logger.debug(f"Document characteristics: {document_analysis.characteristics}")
                self._logger.debug(f"Processing recommendations: {recommendations}")

            # Step 7: Format to Markdown
            self._logger.debug("Formatting to Markdown...")
            self._markdown_formatter.format_to_file(document_with_headings, str(cli_args.output_file))

            self._logger.info(f"Successfully created Markdown output: {cli_args.output_file}")

            # Step 8: Quality validation (if enabled)
            if document_analysis.confidence < 0.5:
                self._output_handler.warning(
                    f"Low confidence in document type detection ({document_analysis.confidence:.2f}). "
                    "Results may not be optimal. Consider manual review."
                )

        except OSError as e:
            raise FileSystemError(
                f"File operation failed: {e}",
                operation="process",
                file_path=str(cli_args.input_file)
            ) from e
        except ValueError as e:
            raise InvalidPdfError(
                f"Invalid PDF format: {e}",
                file_path=str(cli_args.input_file)
            ) from e
        except Exception as e:
            # Enhanced error reporting with document analysis context
            error_context = ""
            try:
                if 'document_analysis' in locals():
                    error_context = f" (Document type: {document_analysis.document_type.value})"
            except:
                pass  # Ignore errors in error reporting

            raise ProcessingError(
                f"PDF processing failed: {e}{error_context}",
                stage="convert",
                file_path=str(cli_args.input_file)
            ) from e

    def _integrate_list_blocks_into_document(
        self,
        target_document,
        source_document,
        list_blocks
    ) -> None:
        """Integrate detected list blocks into the document structure.
        
        This method merges list blocks with existing paragraph/text blocks,
        replacing text that was identified as list content with proper ListBlock objects.
        
        Args:
            target_document: Document to populate with integrated blocks
            source_document: Original document with paragraph blocks
            list_blocks: Detected list blocks to integrate
        """
        # For now, implement a simple strategy:
        # 1. Add all non-list blocks from source
        # 2. Add all list blocks
        # Future enhancement: merge based on y-position to maintain proper order

        # Extract list item text for comparison
        list_item_texts = set()
        for list_block in list_blocks:
            for item in list_block.items:
                # Remove leading markers for comparison
                clean_text = item.content.strip()
                list_item_texts.add(clean_text)

        # Add blocks from source, skipping those that are now represented as lists
        for block in source_document.blocks:
            block_text = ""
            if hasattr(block, 'content'):
                block_text = block.content.strip()
            elif hasattr(block, 'lines'):
                block_text = " ".join(line.text.strip() for line in block.lines)

            # Skip blocks that are now represented as list items
            is_list_content = any(
                clean_text in block_text or block_text in clean_text
                for clean_text in list_item_texts
            )

            if not is_list_content:
                target_document.add_block(block)

        # Add all detected list blocks
        for list_block in list_blocks:
            target_document.add_block(list_block)

    def _integrate_code_blocks_into_document(
        self,
        target_document,
        source_document,
        code_blocks
    ) -> None:
        """Integrate detected code blocks into the document structure.
        
        This method merges code blocks with existing paragraph/text blocks,
        replacing text that was identified as code content with proper CodeBlock objects.
        
        Args:
            target_document: Document to populate with integrated blocks
            source_document: Original document with paragraph blocks
            code_blocks: Detected code blocks to integrate
        """
        # Extract code block text for comparison
        code_block_texts = set()
        for code_block in code_blocks:
            # Use the full content of the code block for comparison
            clean_text = code_block.content.strip()
            code_block_texts.add(clean_text)

            # Also add individual lines for more flexible matching
            for line in code_block.lines:
                line_text = line.text.strip()
                if line_text:
                    code_block_texts.add(line_text)

        # Add blocks from source, skipping those that are now represented as code blocks
        for block in source_document.blocks:
            block_text = ""
            if hasattr(block, 'content'):
                block_text = block.content.strip()
            elif hasattr(block, 'lines'):
                block_text = " ".join(line.text.strip() for line in block.lines)

            # Skip blocks that are now represented as code blocks
            is_code_content = any(
                clean_text in block_text or block_text in clean_text
                for clean_text in code_block_texts
            )

            if not is_code_content:
                target_document.add_block(block)

        # Add all detected code blocks
        for code_block in code_blocks:
            target_document.add_block(code_block)

    def _setup_logging(self) -> logging.Logger:
        """Set up application logging.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self._config.app_name)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        # Configure logging level
        log_level = getattr(logging, self._config.logging.level.upper())
        logger.setLevel(log_level)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(self._config.logging.format)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # Add file handler if configured
        if self._config.logging.enable_file_logging and self._config.logging.log_file_path:
            try:
                file_handler = logging.FileHandler(self._config.logging.log_file_path)
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except OSError as e:
                # Log to console if file logging fails
                logger.warning(f"Cannot create log file: {e}")

        return logger

    def _configure_logging_for_args(self, cli_args: CliArguments) -> None:
        """Configure logging based on CLI arguments.
        
        Args:
            cli_args: Parsed CLI arguments
        """
        if cli_args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            self._logger.setLevel(logging.DEBUG)
            for handler in self._logger.handlers:
                handler.setLevel(logging.DEBUG)
        elif cli_args.verbose:
            logging.getLogger().setLevel(logging.INFO)
            self._logger.setLevel(logging.INFO)
            for handler in self._logger.handlers:
                handler.setLevel(logging.INFO)
        elif cli_args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
            self._logger.setLevel(logging.ERROR)
            for handler in self._logger.handlers:
                handler.setLevel(logging.ERROR)


def main() -> NoReturn:
    """Main entry point for the CLI application.
    
    This function serves as the console script entry point and handles
    the application lifecycle and exit codes.
    """
    cli = PdfToMarkdownCli()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
