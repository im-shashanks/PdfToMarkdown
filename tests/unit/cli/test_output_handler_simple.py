"""Simple unit tests for CLI output handler to improve coverage."""

import sys
import pytest
from unittest.mock import Mock, patch

from pdf2markdown.cli.output_handler import OutputHandler
from pdf2markdown.core.config import ApplicationConfig


class TestOutputHandlerBasic:
    """Basic test cases for OutputHandler to improve coverage."""
    
    def test_output_handler_initialization(self):
        """Test OutputHandler initialization."""
        config = ApplicationConfig()
        handler = OutputHandler(config, use_rich=False)
        
        assert handler._config == config
        assert handler._use_rich == False
    
    def test_success_message(self):
        """Test success message output."""
        config = ApplicationConfig()
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.success("Test message")
            mock_print.assert_called_with("SUCCESS: Test message", file=sys.stderr)
    
    def test_error_message(self):
        """Test error message output."""
        config = ApplicationConfig()
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.error("Error message")
            mock_print.assert_called_with("ERROR: Error message", file=sys.stderr)
    
    def test_warning_message(self):
        """Test warning message output."""
        config = ApplicationConfig()
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.warning("Warning message")
            mock_print.assert_called_with("WARNING: Warning message", file=sys.stderr)
    
    def test_info_message(self):
        """Test info message output."""
        config = ApplicationConfig()
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.info("Info message")
            mock_print.assert_called_with("INFO: Info message", file=sys.stderr)
    
    def test_debug_message_disabled(self):
        """Test debug message when debug is disabled."""
        config = ApplicationConfig(debug=False)
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.debug("Debug message")
            mock_print.assert_not_called()  # Should not print when debug is disabled
    
    def test_debug_message_enabled(self):
        """Test debug message when debug is enabled."""
        config = ApplicationConfig(debug=True)
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.debug("Debug message")
            mock_print.assert_called_with("DEBUG: Debug message", file=sys.stderr)
    
    def test_print_header(self):
        """Test header printing."""
        config = ApplicationConfig()
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.print_header("Test Header")
            
            calls = mock_print.call_args_list
            assert len(calls) >= 2  # Header and empty line
            assert any("Test Header" in str(call) for call in calls)
    
    def test_print_header_with_subtitle(self):
        """Test header printing with subtitle."""
        config = ApplicationConfig()
        handler = OutputHandler(config, use_rich=False)
        
        with patch('builtins.print') as mock_print:
            handler.print_header("Test Header", "Subtitle")
            
            calls = mock_print.call_args_list
            assert len(calls) >= 3  # Header, subtitle, and empty line
            assert any("Test Header" in str(call) for call in calls)
            assert any("Subtitle" in str(call) for call in calls)