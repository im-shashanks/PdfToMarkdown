"""
Unit tests for __main__.py module execution.

Tests the module entry point functionality to ensure the package
can be executed correctly with `python -m pdf2markdown`.
"""

import sys
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from pdf2markdown.__main__ import main


class TestMainModule:
    """Test suite for __main__.py module execution."""

    @patch('pdf2markdown.__main__.PdfToMarkdownCli')
    @patch('sys.exit')
    def test_main_creates_cli_and_runs_with_args(self, mock_exit: MagicMock, mock_cli_class: MagicMock) -> None:
        """Test that main() creates CLI instance and runs with command line args."""
        # Arrange
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0
        
        test_args = ['test.pdf', '--output', 'test.md']
        
        with patch.object(sys, 'argv', ['pdf2markdown'] + test_args):
            # Act
            main()
        
        # Assert
        mock_cli_class.assert_called_once()
        mock_cli_instance.run.assert_called_once_with(test_args)
        mock_exit.assert_called_once_with(0)

    @patch('pdf2markdown.__main__.PdfToMarkdownCli')
    @patch('sys.exit')
    def test_main_exits_with_cli_return_code(self, mock_exit: MagicMock, mock_cli_class: MagicMock) -> None:
        """Test that main() exits with the return code from CLI."""
        # Arrange
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 2  # Error exit code
        
        with patch.object(sys, 'argv', ['pdf2markdown', 'nonexistent.pdf']):
            # Act
            main()
        
        # Assert
        mock_exit.assert_called_once_with(2)

    @patch('pdf2markdown.__main__.PdfToMarkdownCli')
    @patch('sys.exit')
    def test_main_handles_empty_args(self, mock_exit: MagicMock, mock_cli_class: MagicMock) -> None:
        """Test that main() handles empty command line arguments."""
        # Arrange
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 2  # Error for missing args
        
        with patch.object(sys, 'argv', ['pdf2markdown']):
            # Act
            main()
        
        # Assert
        mock_cli_class.assert_called_once()
        mock_cli_instance.run.assert_called_once_with([])
        mock_exit.assert_called_once_with(2)

    @patch('pdf2markdown.__main__.PdfToMarkdownCli')
    @patch('sys.exit')
    def test_main_passes_help_flag(self, mock_exit: MagicMock, mock_cli_class: MagicMock) -> None:
        """Test that main() properly passes help flag to CLI."""
        # Arrange
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0  # Success for help
        
        with patch.object(sys, 'argv', ['pdf2markdown', '--help']):
            # Act
            main()
        
        # Assert
        mock_cli_instance.run.assert_called_once_with(['--help'])
        mock_exit.assert_called_once_with(0)

    @patch('pdf2markdown.__main__.PdfToMarkdownCli')
    @patch('sys.exit')
    def test_main_passes_version_flag(self, mock_exit: MagicMock, mock_cli_class: MagicMock) -> None:
        """Test that main() properly passes version flag to CLI."""
        # Arrange
        mock_cli_instance = MagicMock()
        mock_cli_class.return_value = mock_cli_instance
        mock_cli_instance.run.return_value = 0  # Success for version
        
        with patch.object(sys, 'argv', ['pdf2markdown', '--version']):
            # Act
            main()
        
        # Assert
        mock_cli_instance.run.assert_called_once_with(['--version'])
        mock_exit.assert_called_once_with(0)