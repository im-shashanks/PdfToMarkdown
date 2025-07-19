"""
Unit tests for CLI argument parsing.

Tests argument parsing, validation, and error handling functionality
following the AAA pattern with comprehensive coverage of edge cases.
"""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from pdf2markdown.cli.argument_parser import (
    CliArguments,
    ArgumentParser,
    create_argument_parser,
)
from pdf2markdown.core.exceptions import ValidationError
from pdf2markdown.core.config import ApplicationConfig, ProcessingConfig


class TestCliArguments:
    """Test suite for CliArguments value object."""
    
    def test_creates_with_required_parameters(self) -> None:
        """Test creating CliArguments with required parameters."""
        # Arrange
        input_file = Path("test.pdf")
        
        # Act
        args = CliArguments(input_file)
        
        # Assert
        assert args.input_file == input_file
        assert args.output_file == Path("test.md")
        assert args.debug is False
        assert args.verbose is False
        assert args.quiet is False
        assert args.force is False
    
    def test_creates_with_all_parameters(self) -> None:
        """Test creating CliArguments with all parameters."""
        # Arrange
        input_file = Path("document.pdf")
        output_file = Path("output.md")
        
        # Act
        args = CliArguments(
            input_file=input_file,
            output_file=output_file,
            debug=True,
            verbose=True,
            quiet=False,
            force=True
        )
        
        # Assert
        assert args.input_file == input_file
        assert args.output_file == output_file
        assert args.debug is True
        assert args.verbose is True  # Should remain True even with debug=True
        assert args.quiet is False
        assert args.force is True
    
    def test_debug_implies_verbose(self) -> None:
        """Test that debug=True implies verbose=True."""
        # Arrange
        input_file = Path("test.pdf")
        
        # Act
        args = CliArguments(input_file, debug=True, verbose=False)
        
        # Assert
        assert args.debug is True
        assert args.verbose is True  # Should be True due to debug=True
    
    def test_generates_default_output_path(self) -> None:
        """Test automatic generation of output file path."""
        # Arrange
        input_file = Path("/path/to/document.pdf")
        
        # Act
        args = CliArguments(input_file)
        
        # Assert
        assert args.output_file == Path("/path/to/document.md")
    
    def test_validates_verbose_and_quiet_conflict(self) -> None:
        """Test validation of conflicting verbose and quiet options."""
        # Arrange
        input_file = Path("test.pdf")
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CliArguments(input_file, verbose=True, quiet=True)
        
        assert "Cannot specify both --verbose and --quiet" in str(exc_info.value)
        assert exc_info.value.details["field"] == "output_mode"
    
    def test_validates_input_file_extension(self) -> None:
        """Test validation of input file extension."""
        # Arrange
        input_file = Path("document.txt")
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CliArguments(input_file)
        
        assert "Input file must have .pdf extension" in str(exc_info.value)
        assert exc_info.value.details["field"] == "input_file"
    
    def test_to_dict_returns_serializable_representation(self) -> None:
        """Test that to_dict returns a serializable dictionary."""
        # Arrange
        input_file = Path("test.pdf")
        output_file = Path("output.md")
        args = CliArguments(
            input_file=input_file,
            output_file=output_file,
            debug=True,
            verbose=True,
            quiet=False,
            force=True
        )
        
        # Act
        result = args.to_dict()
        
        # Assert
        expected = {
            'input_file': str(input_file),
            'output_file': str(output_file),
            'debug': True,
            'verbose': True,
            'quiet': False,
            'force': True,
        }
        assert result == expected


class TestArgumentParser:
    """Test suite for ArgumentParser class."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = ApplicationConfig()
        self.parser = ArgumentParser(self.config)
        
        # Create temporary PDF file for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_pdf = self.temp_dir / "test.pdf"
        self.test_pdf.write_bytes(b"%PDF-1.4\n%EOF\n")  # Minimal PDF content
    
    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parses_minimal_arguments(self) -> None:
        """Test parsing minimal required arguments."""
        # Arrange
        args = [str(self.test_pdf)]
        
        # Act
        result = self.parser.parse_args(args)
        
        # Assert
        assert isinstance(result, CliArguments)
        assert result.input_file == self.test_pdf
        assert result.output_file == self.test_pdf.with_suffix('.md')
        assert result.debug is False
        assert result.verbose is False
        assert result.quiet is False
        assert result.force is False
    
    def test_parses_all_arguments(self) -> None:
        """Test parsing all available arguments."""
        # Arrange
        output_file = self.temp_dir / "output.md"
        args = [
            str(self.test_pdf),
            "--output", str(output_file),
            "--debug",
            "--verbose",
            "--force"
        ]
        
        # Act
        result = self.parser.parse_args(args)
        
        # Assert
        assert result.input_file == self.test_pdf
        assert result.output_file == output_file
        assert result.debug is True
        assert result.verbose is True
        assert result.force is True
    
    def test_parses_short_options(self) -> None:
        """Test parsing short option forms."""
        # Arrange
        output_file = self.temp_dir / "output.md"
        args = [
            str(self.test_pdf),
            "-o", str(output_file),
            "-v",
            "-q",
            "-f"
        ]
        
        # Act
        result = self.parser.parse_args(args)
        
        # Assert
        assert result.input_file == self.test_pdf
        assert result.output_file == output_file
        assert result.verbose is True
        assert result.quiet is True
        assert result.force is True
    
    def test_validates_input_file_exists(self) -> None:
        """Test validation that input file must exist."""
        # Arrange
        non_existent_file = self.temp_dir / "nonexistent.pdf"
        args = [str(non_existent_file)]
        
        # Act & Assert
        with pytest.raises(SystemExit):  # argparse raises SystemExit
            self.parser.parse_args(args)
    
    def test_validates_input_file_is_regular_file(self) -> None:
        """Test validation that input must be a regular file."""
        # Arrange
        directory = self.temp_dir / "directory.pdf"
        directory.mkdir()
        args = [str(directory)]
        
        # Act & Assert
        with pytest.raises(SystemExit):  # argparse raises SystemExit
            self.parser.parse_args(args)
    
    def test_validates_input_file_extension(self) -> None:
        """Test validation of input file extension."""
        # Arrange
        text_file = self.temp_dir / "document.txt"
        text_file.write_text("not a pdf")
        args = [str(text_file)]
        
        # Act & Assert
        with pytest.raises(SystemExit):  # argparse raises SystemExit
            self.parser.parse_args(args)
    
    def test_validates_file_size_limit(self) -> None:
        """Test validation of file size limits."""
        # Arrange
        # Create a large file that exceeds the limit
        large_file = self.temp_dir / "large.pdf"
        large_size = self.config.processing.max_file_size_mb * 1024 * 1024 + 1
        
        with open(large_file, 'wb') as f:
            f.write(b"%PDF-1.4\n")
            f.seek(large_size - 1)
            f.write(b"\0")
        
        args = [str(large_file)]
        
        # Act & Assert
        with pytest.raises(SystemExit):  # argparse raises SystemExit
            self.parser.parse_args(args)
    
    @patch('os.access')
    def test_validates_file_permissions(self, mock_access: Mock) -> None:
        """Test validation of file read permissions."""
        # Arrange
        mock_access.return_value = False  # Simulate no read permission
        args = [str(self.test_pdf)]
        
        # Act & Assert
        with pytest.raises(SystemExit):  # argparse raises SystemExit
            self.parser.parse_args(args)
    
    def test_print_help_outputs_usage(self, capsys) -> None:
        """Test that print_help outputs usage information."""
        # Arrange & Act
        self.parser.print_help()
        
        # Assert
        captured = capsys.readouterr()
        assert "pdf2md" in captured.out
        assert "Convert PDF documents" in captured.out
        assert "usage:" in captured.out.lower()
    
    def test_version_option_displays_version(self) -> None:
        """Test that --version displays version information."""
        # Arrange
        args = ["--version"]
        
        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(args)
        
        # SystemExit with code 0 indicates success (version displayed)
        assert exc_info.value.code == 0
    
    def test_help_option_displays_help(self) -> None:
        """Test that --help displays help information."""
        # Arrange
        args = ["--help"]
        
        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(args)
        
        # SystemExit with code 0 indicates success (help displayed)
        assert exc_info.value.code == 0
    
    def test_handles_missing_arguments(self) -> None:
        """Test handling of missing required arguments."""
        # Arrange
        args = []
        
        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(args)
        
        # SystemExit with non-zero code indicates error
        assert exc_info.value.code != 0
    
    def test_handles_invalid_options(self) -> None:
        """Test handling of invalid command-line options."""
        # Arrange
        args = [str(self.test_pdf), "--invalid-option"]
        
        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(args)
        
        # SystemExit with non-zero code indicates error
        assert exc_info.value.code != 0


class TestCreateArgumentParser:
    """Test suite for create_argument_parser factory function."""
    
    def test_creates_argument_parser_instance(self) -> None:
        """Test that factory creates ArgumentParser instance."""
        # Arrange
        config = ApplicationConfig()
        
        # Act
        parser = create_argument_parser(config)
        
        # Assert
        assert isinstance(parser, ArgumentParser)
    
    def test_passes_config_to_parser(self) -> None:
        """Test that factory passes config to parser correctly."""
        # Arrange
        config = ApplicationConfig(
            processing=ProcessingConfig(max_file_size_mb=50)
        )
        
        # Act
        parser = create_argument_parser(config)
        
        # Assert
        assert parser._config.processing.max_file_size_mb == 50