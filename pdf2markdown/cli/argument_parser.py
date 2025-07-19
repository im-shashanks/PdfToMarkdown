"""
Command-line argument parsing for PdfToMarkdown.

This module provides a clean interface for parsing command-line arguments
following the Single Responsibility Principle and providing comprehensive
validation and help text generation.
"""

import argparse
import os
from pathlib import Path
from typing import Optional
from typing import Sequence

from pdf2markdown.core.config import ApplicationConfig
from pdf2markdown.core.exceptions import ValidationError


class CliArguments:
    """Value object containing parsed command-line arguments.
    
    This immutable data structure holds validated command-line arguments
    with proper type conversion and default value handling.
    """

    def __init__(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        debug: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        force: bool = False
    ) -> None:
        """Initialize CLI arguments with validation.
        
        Args:
            input_file: Path to input PDF file
            output_file: Optional path to output Markdown file
            debug: Enable debug mode with verbose output
            verbose: Enable verbose output
            quiet: Suppress non-error output
            force: Overwrite existing output files
            
        Raises:
            ValidationError: If argument combination is invalid
        """
        self.input_file = input_file
        self.output_file = output_file or self._generate_output_path(input_file)
        self.debug = debug
        self.verbose = verbose or debug  # Debug implies verbose
        self.quiet = quiet
        self.force = force

        self._validate()

    def _generate_output_path(self, input_file: Path) -> Path:
        """Generate default output file path from input file.
        
        Args:
            input_file: Input PDF file path
            
        Returns:
            Generated output file path with .md extension
        """
        return input_file.with_suffix('.md')

    def _validate(self) -> None:
        """Validate argument combinations and constraints.
        
        Raises:
            ValidationError: If arguments are invalid or conflicting
        """
        if self.verbose and self.quiet:
            raise ValidationError(
                "Cannot specify both --verbose and --quiet options",
                field="output_mode"
            )

        if not self.input_file.suffix.lower() == '.pdf':
            raise ValidationError(
                f"Input file must have .pdf extension: {self.input_file}",
                field="input_file"
            )

    def to_dict(self) -> dict:
        """Convert arguments to dictionary for logging/debugging.
        
        Returns:
            Dictionary representation of arguments
        """
        return {
            'input_file': str(self.input_file),
            'output_file': str(self.output_file),
            'debug': self.debug,
            'verbose': self.verbose,
            'quiet': self.quiet,
            'force': self.force,
        }


class ArgumentParser:
    """Command-line argument parser for PdfToMarkdown application.
    
    This class follows the Single Responsibility Principle by focusing
    solely on argument parsing and validation, delegating business logic
    to other components.
    """

    def __init__(self, config: ApplicationConfig) -> None:
        """Initialize argument parser with application configuration.
        
        Args:
            config: Application configuration for defaults and validation
        """
        self._config = config
        self._parser = self._create_parser()

    def parse_args(self, args: Optional[Sequence[str]] = None) -> CliArguments:
        """Parse command-line arguments and return validated object.
        
        Args:
            args: Optional sequence of arguments to parse (defaults to sys.argv)
            
        Returns:
            Validated CLI arguments object
            
        Raises:
            ValidationError: If arguments are invalid
            SystemExit: If help is requested or parsing fails
        """
        try:
            parsed_args = self._parser.parse_args(args)
            return self._convert_to_cli_arguments(parsed_args)
        except argparse.ArgumentError as e:
            raise ValidationError(f"Invalid command line arguments: {e}")

    def print_help(self) -> None:
        """Print help text to stdout."""
        self._parser.print_help()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog='pdf2md',
            description=(
                'Convert PDF documents to clean, structured Markdown format. '
                'Supports tables, headings, and text formatting with enterprise-grade '
                'reliability and performance.'
            ),
            epilog=(
                'Examples:\n'
                '  pdf2md document.pdf                    # Convert to document.md\n'
                '  pdf2md report.pdf --output report.md   # Specify output file\n'
                '  pdf2md file.pdf --debug                # Enable debug output\n'
                '  pdf2md large.pdf --force               # Overwrite existing files'
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=True
        )

        # Positional arguments
        parser.add_argument(
            'input_file',
            type=self._validate_input_file,
            help='Path to the PDF file to convert'
        )

        # Optional arguments
        parser.add_argument(
            '-o', '--output',
            type=Path,
            dest='output_file',
            help=(
                'Output Markdown file path. If not specified, uses input '
                'filename with .md extension.'
            )
        )

        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode with verbose output and detailed logging'
        )

        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Enable verbose output (progress and status information)'
        )

        parser.add_argument(
            '-q', '--quiet',
            action='store_true',
            help='Suppress all output except errors'
        )

        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='Overwrite existing output files without prompting'
        )

        parser.add_argument(
            '--version',
            action='version',
            version=f'%(prog)s {self._config.version}'
        )

        return parser

    def _validate_input_file(self, file_path: str) -> Path:
        """Validate input file path and convert to Path object.
        
        Args:
            file_path: String path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            argparse.ArgumentTypeError: If file is invalid
        """
        try:
            path = Path(file_path)
            resolved_path = path.resolve()

            # Check if file exists
            if not resolved_path.exists():
                raise argparse.ArgumentTypeError(f"File not found: {file_path}")

            # Check if it's a regular file
            if not resolved_path.is_file():
                raise argparse.ArgumentTypeError(f"Not a regular file: {file_path}")

            # Check file extension
            if path.suffix.lower() != '.pdf':
                raise argparse.ArgumentTypeError(
                    f"File must have .pdf extension: {file_path}"
                )

            # Check file size
            max_size = self._config.processing.max_file_size_mb * 1024 * 1024
            if resolved_path.stat().st_size > max_size:
                max_mb = self._config.processing.max_file_size_mb
                raise argparse.ArgumentTypeError(
                    f"File size exceeds {max_mb}MB limit: {file_path}"
                )

            # Check file permissions
            if not os.access(resolved_path, os.R_OK):
                raise argparse.ArgumentTypeError(f"File is not readable: {file_path}")

            return path

        except OSError as e:
            raise argparse.ArgumentTypeError(f"Cannot access file {file_path}: {e}")

    def _convert_to_cli_arguments(self, parsed_args: argparse.Namespace) -> CliArguments:
        """Convert argparse Namespace to CliArguments object.
        
        Args:
            parsed_args: Parsed arguments from argparse
            
        Returns:
            Validated CliArguments object
        """
        return CliArguments(
            input_file=parsed_args.input_file,
            output_file=parsed_args.output_file,
            debug=parsed_args.debug,
            verbose=parsed_args.verbose,
            quiet=parsed_args.quiet,
            force=parsed_args.force
        )


def create_argument_parser(config: ApplicationConfig) -> ArgumentParser:
    """Factory function to create configured argument parser.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured ArgumentParser instance
    """
    return ArgumentParser(config)
