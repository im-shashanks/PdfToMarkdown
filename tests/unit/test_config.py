"""
Unit tests for configuration management.

Tests configuration loading, validation, and environment variable handling
following the AAA pattern with comprehensive edge case coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from pdf2markdown.core.config import (
    ProcessingConfig,
    LoggingConfig,
    ApplicationConfig,
    ConfigurationManager,
)
from pdf2markdown.core.exceptions import ValidationError, ConfigurationError


class TestProcessingConfig:
    """Test suite for ProcessingConfig value object."""
    
    def test_creates_with_default_values(self) -> None:
        """Test creating ProcessingConfig with default values."""
        # Arrange & Act
        config = ProcessingConfig()
        
        # Assert
        assert config.max_file_size_mb == 100
        assert config.processing_timeout_seconds == 300
        assert config.memory_limit_mb == 512
        assert config.extract_tables is True
        assert config.extract_images is False
        assert config.preserve_formatting is True
        assert config.markdown_dialect == "gfm"
        assert config.include_metadata is True
        assert config.wrap_long_lines is True
        assert config.line_length == 80
    
    def test_creates_with_custom_values(self) -> None:
        """Test creating ProcessingConfig with custom values."""
        # Arrange & Act
        config = ProcessingConfig(
            max_file_size_mb=50,
            processing_timeout_seconds=600,
            memory_limit_mb=1024,
            extract_tables=False,
            extract_images=True,
            preserve_formatting=False,
            markdown_dialect="commonmark",
            include_metadata=False,
            wrap_long_lines=False,
            line_length=120
        )
        
        # Assert
        assert config.max_file_size_mb == 50
        assert config.processing_timeout_seconds == 600
        assert config.memory_limit_mb == 1024
        assert config.extract_tables is False
        assert config.extract_images is True
        assert config.preserve_formatting is False
        assert config.markdown_dialect == "commonmark"
        assert config.include_metadata is False
        assert config.wrap_long_lines is False
        assert config.line_length == 120
    
    def test_validates_max_file_size_mb_positive(self) -> None:
        """Test validation of max_file_size_mb must be positive."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(max_file_size_mb=0)
        
        assert "max_file_size_mb must be positive" in str(exc_info.value)
        assert exc_info.value.details["field"] == "max_file_size_mb"
    
    def test_validates_processing_timeout_positive(self) -> None:
        """Test validation of processing_timeout_seconds must be positive."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(processing_timeout_seconds=-1)
        
        assert "processing_timeout_seconds must be positive" in str(exc_info.value)
        assert exc_info.value.details["field"] == "processing_timeout_seconds"
    
    def test_validates_memory_limit_positive(self) -> None:
        """Test validation of memory_limit_mb must be positive."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(memory_limit_mb=0)
        
        assert "memory_limit_mb must be positive" in str(exc_info.value)
        assert exc_info.value.details["field"] == "memory_limit_mb"
    
    def test_validates_markdown_dialect_valid(self) -> None:
        """Test validation of markdown_dialect must be valid."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(markdown_dialect="invalid")
        
        assert "markdown_dialect must be one of" in str(exc_info.value)
        assert exc_info.value.details["field"] == "markdown_dialect"
    
    def test_validates_line_length_positive(self) -> None:
        """Test validation of line_length must be positive."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(line_length=0)
        
        assert "line_length must be positive" in str(exc_info.value)
        assert exc_info.value.details["field"] == "line_length"
    
    def test_accepts_valid_markdown_dialects(self) -> None:
        """Test that all valid markdown dialects are accepted."""
        # Arrange
        valid_dialects = ["gfm", "commonmark", "basic"]
        
        # Act & Assert
        for dialect in valid_dialects:
            config = ProcessingConfig(markdown_dialect=dialect)
            assert config.markdown_dialect == dialect


class TestLoggingConfig:
    """Test suite for LoggingConfig value object."""
    
    def test_creates_with_default_values(self) -> None:
        """Test creating LoggingConfig with default values."""
        # Arrange & Act
        config = LoggingConfig()
        
        # Assert
        assert config.level == "INFO"
        assert "%(asctime)s" in config.format
        assert config.enable_file_logging is False
        assert config.log_file_path is None
        assert config.max_log_file_size_mb == 10
        assert config.backup_count == 3
    
    def test_creates_with_custom_values(self) -> None:
        """Test creating LoggingConfig with custom values."""
        # Arrange & Act
        config = LoggingConfig(
            level="DEBUG",
            format="%(levelname)s: %(message)s",
            enable_file_logging=True,
            log_file_path="/tmp/app.log",
            max_log_file_size_mb=5,
            backup_count=2
        )
        
        # Assert
        assert config.level == "DEBUG"
        assert config.format == "%(levelname)s: %(message)s"
        assert config.enable_file_logging is True
        assert config.log_file_path == "/tmp/app.log"
        assert config.max_log_file_size_mb == 5
        assert config.backup_count == 2
    
    def test_validates_logging_level_valid(self) -> None:
        """Test validation of logging level must be valid."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(level="INVALID")
        
        assert "Logging level must be one of" in str(exc_info.value)
        assert exc_info.value.details["field"] == "level"
    
    def test_validates_file_logging_requires_path(self) -> None:
        """Test validation that file logging requires log_file_path."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(enable_file_logging=True, log_file_path=None)
        
        assert "log_file_path is required when file logging is enabled" in str(exc_info.value)
        assert exc_info.value.details["field"] == "log_file_path"
    
    def test_validates_max_log_file_size_positive(self) -> None:
        """Test validation of max_log_file_size_mb must be positive."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(max_log_file_size_mb=0)
        
        assert "max_log_file_size_mb must be positive" in str(exc_info.value)
        assert exc_info.value.details["field"] == "max_log_file_size_mb"
    
    def test_accepts_valid_logging_levels(self) -> None:
        """Test that all valid logging levels are accepted."""
        # Arrange
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        # Act & Assert
        for level in valid_levels:
            config = LoggingConfig(level=level)
            assert config.level == level
    
    def test_accepts_lowercase_logging_levels(self) -> None:
        """Test that lowercase logging levels are handled correctly."""
        # Arrange & Act
        config = LoggingConfig(level="debug")
        
        # Assert - validation should convert to uppercase internally
        # This tests the validation logic handles case conversion
        with pytest.raises(ValidationError):
            # The validation should fail for lowercase as it checks uppercase
            pass


class TestApplicationConfig:
    """Test suite for ApplicationConfig aggregate."""
    
    def test_creates_with_default_values(self) -> None:
        """Test creating ApplicationConfig with default values."""
        # Arrange & Act
        config = ApplicationConfig()
        
        # Assert
        assert config.app_name == "pdf2markdown"
        assert config.version == "1.0.0"
        assert config.debug is False
        assert isinstance(config.processing, ProcessingConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.working_directory, Path)
        assert isinstance(config.temp_directory, Path)
    
    def test_creates_with_custom_values(self) -> None:
        """Test creating ApplicationConfig with custom values."""
        # Arrange
        custom_processing = ProcessingConfig(max_file_size_mb=50)
        custom_logging = LoggingConfig(level="DEBUG")
        
        # Act
        config = ApplicationConfig(
            app_name="test-app",
            version="2.0.0",
            debug=True,
            processing=custom_processing,
            logging=custom_logging
        )
        
        # Assert
        assert config.app_name == "test-app"
        assert config.version == "2.0.0"
        assert config.debug is True
        assert config.processing == custom_processing
        assert config.logging == custom_logging
    
    def test_validates_app_name_not_empty(self) -> None:
        """Test validation that app_name cannot be empty."""
        # Arrange & Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            ApplicationConfig(app_name="")
        
        assert "app_name cannot be empty" in str(exc_info.value)
    
    def test_validates_version_not_empty(self) -> None:
        """Test validation that version cannot be empty."""
        # Arrange & Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            ApplicationConfig(version="")
        
        assert "version cannot be empty" in str(exc_info.value)
    
    def test_sets_default_working_directory(self) -> None:
        """Test that default working directory is set to current directory."""
        # Arrange & Act
        config = ApplicationConfig()
        
        # Assert
        assert config.working_directory == Path.cwd()
    
    def test_sets_default_temp_directory(self) -> None:
        """Test that default temp directory is set to system temp."""
        # Arrange & Act
        config = ApplicationConfig()
        
        # Assert
        assert config.temp_directory is not None
        assert config.temp_directory.exists()
    
    def test_validates_working_directory_exists(self) -> None:
        """Test validation that working directory must exist."""
        # Arrange
        non_existent_path = Path("/path/that/does/not/exist")
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            ApplicationConfig(working_directory=non_existent_path)
        
        assert "Working directory does not exist" in str(exc_info.value)


class TestConfigurationManager:
    """Test suite for ConfigurationManager singleton."""
    
    def test_singleton_behavior(self) -> None:
        """Test that ConfigurationManager implements singleton pattern."""
        # Arrange & Act
        manager1 = ConfigurationManager()
        manager2 = ConfigurationManager()
        
        # Assert
        assert manager1 is manager2
    
    def test_get_config_returns_application_config(self) -> None:
        """Test that get_config returns ApplicationConfig instance."""
        # Arrange
        manager = ConfigurationManager()
        
        # Act
        config = manager.get_config()
        
        # Assert
        assert isinstance(config, ApplicationConfig)
    
    @patch.dict(os.environ, {
        "PDF2MD_MAX_FILE_SIZE_MB": "200",
        "PDF2MD_TIMEOUT": "600",
        "PDF2MD_MEMORY_LIMIT_MB": "1024",
        "PDF2MD_EXTRACT_TABLES": "false",
        "PDF2MD_EXTRACT_IMAGES": "true",
        "PDF2MD_PRESERVE_FORMATTING": "false",
        "PDF2MD_MARKDOWN_DIALECT": "commonmark",
        "PDF2MD_INCLUDE_METADATA": "false",
        "PDF2MD_WRAP_LINES": "false",
        "PDF2MD_LINE_LENGTH": "120",
        "PDF2MD_LOG_LEVEL": "DEBUG",
        "PDF2MD_FILE_LOGGING": "true",
        "PDF2MD_LOG_FILE": "/tmp/test.log",
        "PDF2MD_LOG_FILE_SIZE_MB": "5",
        "PDF2MD_LOG_BACKUP_COUNT": "2",
        "PDF2MD_DEBUG": "true",
    })
    def test_loads_configuration_from_environment(self) -> None:
        """Test loading configuration from environment variables."""
        # Arrange
        # Clear singleton to force reload
        ConfigurationManager._instance = None
        ConfigurationManager._config = None
        
        # Act
        manager = ConfigurationManager()
        config = manager.get_config()
        
        # Assert
        assert config.processing.max_file_size_mb == 200
        assert config.processing.processing_timeout_seconds == 600
        assert config.processing.memory_limit_mb == 1024
        assert config.processing.extract_tables is False
        assert config.processing.extract_images is True
        assert config.processing.preserve_formatting is False
        assert config.processing.markdown_dialect == "commonmark"
        assert config.processing.include_metadata is False
        assert config.processing.wrap_long_lines is False
        assert config.processing.line_length == 120
        assert config.logging.level == "DEBUG"
        assert config.logging.enable_file_logging is True
        assert config.logging.log_file_path == "/tmp/test.log"
        assert config.logging.max_log_file_size_mb == 5
        assert config.logging.backup_count == 2
        assert config.debug is True
    
    @patch.dict(os.environ, {
        "PDF2MD_MAX_FILE_SIZE_MB": "invalid",
        "PDF2MD_EXTRACT_TABLES": "invalid",
    })
    def test_handles_invalid_environment_values(self) -> None:
        """Test handling of invalid environment variable values."""
        # Arrange
        # Clear singleton to force reload
        ConfigurationManager._instance = None
        ConfigurationManager._config = None
        
        # Act
        manager = ConfigurationManager()
        config = manager.get_config()
        
        # Assert - should fall back to defaults for invalid values
        assert config.processing.max_file_size_mb == 100  # default
        assert config.processing.extract_tables is True  # default
    
    def teardown_method(self) -> None:
        """Reset singleton after each test."""
        ConfigurationManager._instance = None
        ConfigurationManager._config = None