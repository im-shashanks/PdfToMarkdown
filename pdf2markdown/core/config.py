"""
Configuration management for PdfToMarkdown application.

This module provides centralized configuration handling with validation,
type safety, and environment-specific settings following the
Single Responsibility Principle.
"""

import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Optional

from pdf2markdown.core.exceptions import ConfigurationError
from pdf2markdown.core.exceptions import ValidationError


@dataclass(frozen=True)
class ListDetectionConfig:
    """Configuration for list detection behavior.
    
    This value object encapsulates all list detection configuration
    with validation and default values.
    """

    # Detection settings
    indentation_threshold: float = 10.0  # Points of x-position difference per level
    continuation_indent_threshold: float = 5.0  # Threshold for continuation detection
    max_nesting_level: int = 3  # Maximum supported nesting (0-3)

    # Pattern settings
    enable_bullet_detection: bool = True
    enable_numbered_detection: bool = True
    enable_alphabetic_detection: bool = True
    enable_roman_detection: bool = True
    enable_parenthetical_detection: bool = True

    def __post_init__(self) -> None:
        """Validate list detection configuration."""
        self._validate()

    def _validate(self) -> None:
        """Validate all configuration values."""
        if self.indentation_threshold <= 0:
            raise ValidationError(
                "indentation_threshold must be positive",
                field="indentation_threshold"
            )

        if self.continuation_indent_threshold <= 0:
            raise ValidationError(
                "continuation_indent_threshold must be positive",
                field="continuation_indent_threshold"
            )

        if not 0 <= self.max_nesting_level <= 3:
            raise ValidationError(
                "max_nesting_level must be between 0 and 3",
                field="max_nesting_level"
            )


@dataclass(frozen=True)
class ProcessingConfig:
    """Configuration for PDF processing behavior.
    
    This value object encapsulates all processing-related configuration
    with validation and default values.
    """

    # Performance settings
    max_file_size_mb: int = 100
    processing_timeout_seconds: int = 300
    memory_limit_mb: int = 512

    # Processing options
    extract_tables: bool = True
    extract_images: bool = False
    preserve_formatting: bool = True

    # Output formatting
    markdown_dialect: str = "gfm"  # GitHub Flavored Markdown
    include_metadata: bool = True
    wrap_long_lines: bool = True
    line_length: int = 80

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all configuration values.
        
        Raises:
            ValidationError: If any configuration value is invalid
        """
        if self.max_file_size_mb <= 0:
            raise ValidationError(
                "max_file_size_mb must be positive",
                field="max_file_size_mb"
            )

        if self.processing_timeout_seconds <= 0:
            raise ValidationError(
                "processing_timeout_seconds must be positive",
                field="processing_timeout_seconds"
            )

        if self.memory_limit_mb <= 0:
            raise ValidationError(
                "memory_limit_mb must be positive",
                field="memory_limit_mb"
            )

        valid_dialects = {"gfm", "commonmark", "basic"}
        if self.markdown_dialect not in valid_dialects:
            raise ValidationError(
                f"markdown_dialect must be one of {valid_dialects}",
                field="markdown_dialect"
            )

        if self.line_length <= 0:
            raise ValidationError(
                "line_length must be positive",
                field="line_length"
            )


@dataclass(frozen=True)
class LoggingConfig:
    """Configuration for application logging.
    
    This value object manages logging configuration with proper
    level validation and format specification.
    """

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = False
    log_file_path: Optional[str] = None
    max_log_file_size_mb: int = 10
    backup_count: int = 3

    def __post_init__(self) -> None:
        """Validate logging configuration."""
        self._validate()

    def _validate(self) -> None:
        """Validate logging configuration values.
        
        Raises:
            ValidationError: If any logging configuration value is invalid
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in valid_levels:
            raise ValidationError(
                f"Logging level must be one of {valid_levels}",
                field="level"
            )

        if self.enable_file_logging and not self.log_file_path:
            raise ValidationError(
                "log_file_path is required when file logging is enabled",
                field="log_file_path"
            )

        if self.max_log_file_size_mb <= 0:
            raise ValidationError(
                "max_log_file_size_mb must be positive",
                field="max_log_file_size_mb"
            )


@dataclass(frozen=True)
class ApplicationConfig:
    """Main application configuration container.
    
    This configuration aggregate combines all application settings
    with environment-specific overrides and validation.
    """

    # Core settings
    app_name: str = "pdf2markdown"
    version: str = "1.0.0"
    debug: bool = False

    # Component configurations
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    list_detection: ListDetectionConfig = field(default_factory=ListDetectionConfig)

    # Runtime paths
    working_directory: Optional[Path] = None
    temp_directory: Optional[Path] = None

    def __post_init__(self) -> None:
        """Initialize computed values and validate configuration."""
        # Set default paths if not provided
        if self.working_directory is None:
            object.__setattr__(self, 'working_directory', Path.cwd())

        if self.temp_directory is None:
            import tempfile
            object.__setattr__(self, 'temp_directory', Path(tempfile.gettempdir()))

        self._validate()

    def _validate(self) -> None:
        """Validate application configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.app_name:
            raise ConfigurationError("app_name cannot be empty")

        if not self.version:
            raise ConfigurationError("version cannot be empty")

        if self.working_directory and not self.working_directory.exists():
            raise ConfigurationError(
                f"Working directory does not exist: {self.working_directory}"
            )


class ConfigurationManager:
    """Manages application configuration with environment overrides.
    
    This service follows the Single Responsibility Principle by focusing
    solely on configuration management, including loading from environment
    variables and validation.
    """

    _instance: Optional['ConfigurationManager'] = None
    _config: Optional[ApplicationConfig] = None

    def __new__(cls) -> 'ConfigurationManager':
        """Implement singleton pattern for global configuration access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize configuration manager."""
        if self._config is None:
            self._config = self._load_configuration()

    def get_config(self) -> ApplicationConfig:
        """Get the current application configuration.
        
        Returns:
            Current application configuration instance
        """
        if self._config is None:
            self._config = self._load_configuration()
        return self._config

    def _load_configuration(self) -> ApplicationConfig:
        """Load configuration from environment and defaults.
        
        Returns:
            Loaded and validated application configuration
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            # Load processing configuration
            processing_config = ProcessingConfig(
                max_file_size_mb=self._get_env_int("PDF2MD_MAX_FILE_SIZE_MB", 100),
                processing_timeout_seconds=self._get_env_int("PDF2MD_TIMEOUT", 300),
                memory_limit_mb=self._get_env_int("PDF2MD_MEMORY_LIMIT_MB", 512),
                extract_tables=self._get_env_bool("PDF2MD_EXTRACT_TABLES", True),
                extract_images=self._get_env_bool("PDF2MD_EXTRACT_IMAGES", False),
                preserve_formatting=self._get_env_bool("PDF2MD_PRESERVE_FORMATTING", True),
                markdown_dialect=os.getenv("PDF2MD_MARKDOWN_DIALECT", "gfm"),
                include_metadata=self._get_env_bool("PDF2MD_INCLUDE_METADATA", True),
                wrap_long_lines=self._get_env_bool("PDF2MD_WRAP_LINES", True),
                line_length=self._get_env_int("PDF2MD_LINE_LENGTH", 80),
            )

            # Load logging configuration
            logging_config = LoggingConfig(
                level=os.getenv("PDF2MD_LOG_LEVEL", "INFO").upper(),
                enable_file_logging=self._get_env_bool("PDF2MD_FILE_LOGGING", False),
                log_file_path=os.getenv("PDF2MD_LOG_FILE"),
                max_log_file_size_mb=self._get_env_int("PDF2MD_LOG_FILE_SIZE_MB", 10),
                backup_count=self._get_env_int("PDF2MD_LOG_BACKUP_COUNT", 3),
            )

            # Load list detection configuration
            list_detection_config = ListDetectionConfig(
                indentation_threshold=self._get_env_float("PDF2MD_LIST_INDENT_THRESHOLD", 10.0),
                continuation_indent_threshold=self._get_env_float("PDF2MD_LIST_CONTINUATION_THRESHOLD", 5.0),
                max_nesting_level=self._get_env_int("PDF2MD_LIST_MAX_NESTING", 3),
                enable_bullet_detection=self._get_env_bool("PDF2MD_LIST_ENABLE_BULLETS", True),
                enable_numbered_detection=self._get_env_bool("PDF2MD_LIST_ENABLE_NUMBERED", True),
                enable_alphabetic_detection=self._get_env_bool("PDF2MD_LIST_ENABLE_ALPHABETIC", True),
                enable_roman_detection=self._get_env_bool("PDF2MD_LIST_ENABLE_ROMAN", True),
                enable_parenthetical_detection=self._get_env_bool("PDF2MD_LIST_ENABLE_PARENTHETICAL", True),
            )

            # Create main configuration
            config = ApplicationConfig(
                debug=self._get_env_bool("PDF2MD_DEBUG", False),
                processing=processing_config,
                logging=logging_config,
                list_detection=list_detection_config,
            )

            return config

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def _get_env_float(self, key: str, default: float) -> float:
        """Get float value from environment with fallback.
        
        Args:
            key: Environment variable name
            default: Default value if not found or invalid
            
        Returns:
            Float value from environment or default
        """
        try:
            value = os.getenv(key)
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer value from environment with fallback.
        
        Args:
            key: Environment variable name
            default: Default value if not found or invalid
            
        Returns:
            Integer value from environment or default
        """
        try:
            value = os.getenv(key)
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _get_env_bool(self, key: str, default: bool) -> bool:
        """Get boolean value from environment with fallback.
        
        Args:
            key: Environment variable name
            default: Default value if not found or invalid
            
        Returns:
            Boolean value from environment or default
        """
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        else:
            return default


# Global configuration instance
config_manager = ConfigurationManager()
