"""
Integration tests for CLI application.

Tests the integration between CLI components, argument parsing,
file validation, and output generation following the test pyramid
(20% integration tests).
"""

import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from pdf2markdown.cli.main import PdfToMarkdownCli
from pdf2markdown.core.config import ApplicationConfig


class TestCliIntegration:
    """Integration test suite for CLI application."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test PDF file
        self.test_pdf = self.temp_dir / "test_document.pdf"
        self.test_pdf.write_bytes(b"%PDF-1.4\nTest PDF content\n%EOF\n")
        
        # Set up CLI with test configuration
        self.config = ApplicationConfig(debug=False)
        self.cli = PdfToMarkdownCli(self.config)
    
    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_successful_pdf_conversion_minimal_args(self) -> None:
        """Test successful PDF conversion with minimal arguments."""
        # Arrange
        args = [str(self.test_pdf)]
        expected_output = self.test_pdf.with_suffix('.md')
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        assert expected_output.exists()
        
        # Verify output content
        content = expected_output.read_text()
        assert "Converted from test_document.pdf" in content
        assert str(self.test_pdf) in content
        assert "placeholder" in content.lower()
    
    def test_successful_pdf_conversion_with_output_file(self) -> None:
        """Test successful PDF conversion with custom output file."""
        # Arrange
        custom_output = self.temp_dir / "custom_output.md"
        args = [str(self.test_pdf), "--output", str(custom_output)]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        assert custom_output.exists()
        
        # Verify output content
        content = custom_output.read_text()
        assert "Converted from test_document.pdf" in content
        assert str(custom_output) in content
    
    def test_conversion_with_debug_flag(self) -> None:
        """Test PDF conversion with debug flag enabled."""
        # Arrange
        args = [str(self.test_pdf), "--debug"]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        # Verify debug mode affected the CLI behavior
        assert self.cli._config.debug is False  # Original config unchanged
    
    def test_conversion_with_force_overwrite(self) -> None:
        """Test PDF conversion with force overwrite of existing file."""
        # Arrange
        output_file = self.test_pdf.with_suffix('.md')
        output_file.write_text("Existing content")
        args = [str(self.test_pdf), "--force"]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        assert output_file.exists()
        
        # Verify content was overwritten
        content = output_file.read_text()
        assert "Existing content" not in content
        assert "Converted from test_document.pdf" in content
    
    def test_validation_error_nonexistent_file(self) -> None:
        """Test validation error for non-existent input file."""
        # Arrange
        nonexistent_file = self.temp_dir / "nonexistent.pdf"
        args = [str(nonexistent_file)]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 2  # Validation error exit code
    
    def test_validation_error_invalid_file_extension(self) -> None:
        """Test validation error for invalid file extension."""
        # Arrange
        text_file = self.temp_dir / "document.txt"
        text_file.write_text("Not a PDF")
        args = [str(text_file)]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 2  # Validation error exit code
    
    def test_validation_error_invalid_pdf_content(self) -> None:
        """Test validation error for invalid PDF content."""
        # Arrange
        fake_pdf = self.temp_dir / "fake.pdf"
        fake_pdf.write_text("Not actually a PDF file")
        args = [str(fake_pdf)]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 2  # Validation error exit code
    
    def test_output_validation_error_readonly_directory(self) -> None:
        """Test output validation error for read-only directory."""
        # Arrange
        with patch('os.access') as mock_access:
            mock_access.return_value = False
            args = [str(self.test_pdf)]
            
            # Act
            exit_code = self.cli.run(args)
            
            # Assert
            assert exit_code == 3  # Output validation error exit code
    
    def test_output_validation_error_existing_file_no_force(self) -> None:
        """Test output validation error for existing file without force."""
        # Arrange
        output_file = self.test_pdf.with_suffix('.md')
        output_file.write_text("Existing content")
        args = [str(self.test_pdf)]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 3  # Output validation error exit code
    
    def test_processing_error_handling(self) -> None:
        """Test handling of processing errors during conversion."""
        # Arrange
        # Create a situation that would cause processing to fail
        # by mocking the _process_pdf_file method to raise an exception
        with patch.object(self.cli, '_process_pdf_file') as mock_process:
            mock_process.side_effect = Exception("Simulated processing error")
            args = [str(self.test_pdf)]
            
            # Act
            exit_code = self.cli.run(args)
            
            # Assert
            assert exit_code == 99  # Unexpected error exit code
    
    def test_keyboard_interrupt_handling(self) -> None:
        """Test graceful handling of keyboard interrupt."""
        # Arrange
        with patch.object(self.cli, '_process_pdf_file') as mock_process:
            mock_process.side_effect = KeyboardInterrupt()
            args = [str(self.test_pdf)]
            
            # Act
            exit_code = self.cli.run(args)
            
            # Assert
            assert exit_code == 130  # SIGINT exit code
    
    def test_help_option_displays_help(self, capsys) -> None:
        """Test that help option displays help and exits."""
        # Arrange
        args = ["--help"]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
    
    def test_version_option_displays_version(self) -> None:
        """Test that version option displays version and exits."""
        # Arrange
        args = ["--version"]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
    
    def test_argument_parsing_integration(self) -> None:
        """Test integration between argument parser and CLI."""
        # Arrange
        output_file = self.temp_dir / "integration_test.md"
        args = [
            str(self.test_pdf),
            "--output", str(output_file),
            "--verbose",
            "--force"
        ]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        assert output_file.exists()
        
        # Verify the arguments were processed correctly
        content = output_file.read_text()
        assert str(output_file) in content
    
    def test_file_validation_integration(self) -> None:
        """Test integration between file validator and CLI."""
        # Arrange
        # Create a file that passes basic validation but has warnings
        warning_pdf = self.temp_dir / "warning.pdf"
        warning_pdf.write_bytes(b"%PDF-1.2\nOld PDF version\n%EOF\n")
        args = [str(warning_pdf)]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0  # Should succeed despite warnings
        assert warning_pdf.with_suffix('.md').exists()
    
    def test_configuration_integration(self) -> None:
        """Test integration with configuration management."""
        # Arrange
        # Test with modified configuration
        config = ApplicationConfig(debug=True)
        cli = PdfToMarkdownCli(config)
        args = [str(self.test_pdf)]
        
        # Act
        exit_code = cli.run(args)
        
        # Assert
        assert exit_code == 0
        # Configuration should be preserved throughout execution
        assert config.debug is True
    
    def test_quiet_mode_suppresses_output(self, capsys) -> None:
        """Test that quiet mode suppresses non-error output."""
        # Arrange
        args = [str(self.test_pdf), "--quiet"]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        
        # Check that minimal output was produced
        captured = capsys.readouterr()
        # In quiet mode, there should be no success message
        assert "Successfully converted" not in captured.err
    
    def test_verbose_mode_provides_detailed_output(self, capsys) -> None:
        """Test that verbose mode provides detailed output."""
        # Arrange
        args = [str(self.test_pdf), "--verbose"]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        
        # In verbose mode, there should be processing information
        captured = capsys.readouterr()
        # Should have success message and other verbose output
        assert len(captured.err) > 0  # Some output should be present
    
    def test_end_to_end_workflow(self) -> None:
        """Test complete end-to-end workflow integration."""
        # Arrange
        input_file = self.test_pdf
        output_file = self.temp_dir / "e2e_output.md"
        
        # Test the complete workflow:
        # 1. Parse arguments
        # 2. Validate input file
        # 3. Validate output path
        # 4. Process file
        # 5. Generate output
        args = [str(input_file), "--output", str(output_file), "--force"]
        
        # Act
        exit_code = self.cli.run(args)
        
        # Assert
        assert exit_code == 0
        assert output_file.exists()
        
        # Verify complete workflow execution
        content = output_file.read_text()
        assert "Converted from" in content
        assert str(input_file) in content
        assert str(output_file) in content
        assert "File size:" in content