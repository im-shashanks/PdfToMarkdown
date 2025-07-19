# Architecture Documentation

This document provides a comprehensive overview of the PdfToMarkdown architecture, design decisions, and implementation patterns for developers and contributors.

## Table of Contents

- [Overview](#overview)
- [Architectural Principles](#architectural-principles)
- [System Architecture](#system-architecture)
- [Layer Responsibilities](#layer-responsibilities)
- [Design Patterns](#design-patterns)
- [Data Flow](#data-flow)
- [Component Design](#component-design)
- [Error Handling Strategy](#error-handling-strategy)
- [Configuration Management](#configuration-management)
- [Testing Architecture](#testing-architecture)
- [Performance Considerations](#performance-considerations)
- [Security Architecture](#security-architecture)
- [Future Extensions](#future-extensions)

## Overview

PdfToMarkdown is built using **Clean Architecture** principles with a focus on:

- **Separation of Concerns**: Clear boundaries between business logic, I/O, and presentation
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Testability**: Architecture supports comprehensive unit and integration testing
- **Maintainability**: Code is organized for easy understanding and modification
- **Extensibility**: New features can be added without modifying existing code

### Key Design Goals

1. **Lightweight**: Minimal dependencies, fast startup, efficient processing
2. **Reliable**: Robust error handling, graceful degradation, predictable behavior
3. **Maintainable**: Clean code structure, clear interfaces, comprehensive tests
4. **Extensible**: Plugin architecture, configurable processing pipeline
5. **Developer-Friendly**: Clear APIs, good documentation, easy debugging

## Architectural Principles

### SOLID Principles

#### Single Responsibility Principle (SRP)
Each class has one reason to change and one responsibility:

```python
# Good: Single responsibility
class PdfValidator:
    """Only responsible for PDF validation."""
    def validate_pdf_file(self, file_path: Path) -> ValidationResult:
        pass

class MarkdownGenerator:
    """Only responsible for Markdown generation."""
    def generate_markdown(self, content: PdfContent) -> str:
        pass

# Bad: Multiple responsibilities
class PdfProcessor:
    """Handles validation, parsing, and generation."""
    pass
```

#### Open/Closed Principle (OCP)
Open for extension, closed for modification:

```python
# Extensible design
class ContentConverter(ABC):
    @abstractmethod
    def convert(self, content: str) -> str:
        pass

class TableConverter(ContentConverter):
    def convert(self, content: str) -> str:
        # Table-specific conversion logic
        pass

class HeaderConverter(ContentConverter):
    def convert(self, content: str) -> str:
        # Header-specific conversion logic
        pass
```

#### Liskov Substitution Principle (LSP)
Subtypes must be substitutable for their base types:

```python
# All validators can be used interchangeably
validator: FileValidator = PdfValidator()  # or any other validator
result = validator.validate_file(file_path)
```

#### Interface Segregation Principle (ISP)
Clients depend only on interfaces they use:

```python
# Specific interfaces for different concerns
class Readable(Protocol):
    def read(self) -> bytes: pass

class Writable(Protocol):
    def write(self, data: bytes) -> None: pass

class Validatable(Protocol):
    def validate(self) -> ValidationResult: pass
```

#### Dependency Inversion Principle (DIP)
Depend on abstractions, not concretions:

```python
# High-level module depends on abstraction
class PdfProcessor:
    def __init__(self, parser: PdfParser, generator: MarkdownGenerator):
        self._parser = parser  # Abstraction
        self._generator = generator  # Abstraction
```

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    External Interfaces                  │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │   CLI Interface │  │  Python API     │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │     Use Cases / Application Services                │ │
│  │  - PDF Conversion Use Case                          │ │
│  │  - Validation Use Case                              │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                   Domain Layer                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │       Business Logic / Domain Services              │ │
│  │  - PDF Content Models                               │ │
│  │  - Validation Rules                                 │ │
│  │  - Conversion Algorithms                            │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                Infrastructure Layer                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │        External Dependencies                        │ │
│  │  - File System                                      │ │
│  │  - PDF Libraries (pdfminer.six)                     │ │
│  │  - Logging System                                   │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## System Architecture

### High-Level Component Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                           CLI Application                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │ Argument Parser │  │ Output Handler  │  │ Main CLI App    │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│           │                     │                     │          │
└───────────┼─────────────────────┼─────────────────────┼──────────┘
            │                     │                     │
┌───────────┼─────────────────────┼─────────────────────┼──────────┐
│           │        Core Business Logic                │          │
├───────────┼─────────────────────┼─────────────────────┼──────────┤
│           │                     │                     │          │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐   │
│  │ File Validator  │  │ Configuration   │  │ Exception       │   │
│  │                 │  │ Manager         │  │ Handling        │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
            │                     │                     │
┌───────────┼─────────────────────┼─────────────────────┼──────────┐
│           │        Future Domain Layer               │          │
├───────────┼─────────────────────┼─────────────────────┼──────────┤
│           │                     │                     │          │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐   │
│  │ PDF Content     │  │ Markdown        │  │ Processing      │   │
│  │ Models          │  │ Generator       │  │ Pipeline        │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
            │                     │                     │
┌───────────┼─────────────────────┼─────────────────────┼──────────┐
│           │     Infrastructure Layer                 │          │
├───────────┼─────────────────────┼─────────────────────┼──────────┤
│           │                     │                     │          │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐   │
│  │ PDF Parser      │  │ File System     │  │ Logging         │   │
│  │ (pdfminer.six)  │  │ Operations      │  │ System          │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
pdf2markdown/
├── cli/                    # CLI Interface Layer
│   ├── __init__.py
│   ├── argument_parser.py  # Command-line argument parsing
│   ├── main.py            # Main CLI application orchestrator
│   └── output_handler.py  # User output formatting and display
│
├── core/                  # Core Business Logic Layer
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exception hierarchy
│   └── file_validator.py # File validation business rules
│
├── domain/               # Domain Layer (Future)
│   ├── __init__.py
│   ├── models/          # Domain models and entities
│   ├── services/        # Domain services
│   └── value_objects/   # Value objects and data structures
│
├── infrastructure/      # Infrastructure Layer (Future)
│   ├── __init__.py
│   ├── pdf/            # PDF parsing implementations
│   ├── filesystem/     # File system operations
│   └── logging/        # Logging implementations
│
└── __init__.py
```

## Layer Responsibilities

### CLI Layer (`pdf2markdown/cli/`)

**Purpose**: Handle user interaction and orchestrate application flow

**Responsibilities**:
- Parse command-line arguments
- Validate input parameters
- Coordinate business logic execution
- Format and display output to users
- Handle user interruptions (Ctrl+C)

**Key Components**:
- `ArgumentParser`: Parse and validate CLI arguments
- `PdfToMarkdownCli`: Main application orchestrator
- `OutputHandler`: Format user-facing messages

**Dependencies**: Core layer only (no direct infrastructure dependencies)

### Core Layer (`pdf2markdown/core/`)

**Purpose**: Implement business logic and application rules

**Responsibilities**:
- Define business rules and validation logic
- Manage application configuration
- Define custom exceptions and error handling
- Coordinate between CLI and future domain layers

**Key Components**:
- `ApplicationConfig`: Configuration management
- `FileValidator`: Business rules for file validation
- `PdfToMarkdownError`: Exception hierarchy

**Dependencies**: No dependencies on outer layers

### Domain Layer (`pdf2markdown/domain/`) *Future*

**Purpose**: Core business entities and domain logic

**Responsibilities**:
- Model PDF content structure
- Define conversion algorithms
- Implement business rules for content processing
- Manage domain-specific value objects

**Future Components**:
- `PdfDocument`: Aggregate root for PDF content
- `MarkdownContent`: Value object for generated content
- `ConversionStrategy`: Domain service for conversion logic

### Infrastructure Layer (`pdf2markdown/infrastructure/`) *Future*

**Purpose**: Handle external dependencies and technical concerns

**Responsibilities**:
- PDF parsing implementation
- File system operations
- Logging infrastructure
- External service integrations

**Future Components**:
- `PdfMinerParser`: PDF parsing implementation
- `FileSystemService`: File operations
- `LoggingService`: Structured logging

## Design Patterns

### Factory Pattern

Used for object creation with proper dependency injection:

```python
def create_argument_parser(config: ApplicationConfig) -> ArgumentParser:
    """Factory function for creating configured argument parser."""
    return ArgumentParser(config)

def create_file_validator(config: ApplicationConfig) -> FileValidator:
    """Factory function for creating configured file validator."""
    return FileValidator(config)

def create_output_handler(config: ApplicationConfig) -> OutputHandler:
    """Factory function for creating configured output handler."""
    return OutputHandler(config)
```

### Strategy Pattern

For different processing algorithms:

```python
# Future implementation
class ConversionStrategy(ABC):
    @abstractmethod
    def convert(self, pdf_content: PdfContent) -> MarkdownContent:
        pass

class StandardConversionStrategy(ConversionStrategy):
    def convert(self, pdf_content: PdfContent) -> MarkdownContent:
        # Standard conversion algorithm
        pass

class AdvancedConversionStrategy(ConversionStrategy):
    def convert(self, pdf_content: PdfContent) -> MarkdownContent:
        # Advanced conversion with table support
        pass
```

### Repository Pattern

For data access abstraction:

```python
# Future implementation
class PdfRepository(ABC):
    @abstractmethod
    def load_pdf(self, file_path: Path) -> PdfDocument:
        pass

class FileSystemPdfRepository(PdfRepository):
    def load_pdf(self, file_path: Path) -> PdfDocument:
        # Load PDF from file system
        pass
```

### Command Pattern

For operation encapsulation:

```python
# Future implementation
class ConvertPdfCommand:
    def __init__(self, input_path: Path, output_path: Path, strategy: ConversionStrategy):
        self.input_path = input_path
        self.output_path = output_path
        self.strategy = strategy
    
    def execute(self) -> ConversionResult:
        # Execute conversion command
        pass
```

### Observer Pattern

For progress reporting and event handling:

```python
# Future implementation
class ConversionObserver(ABC):
    @abstractmethod
    def on_progress(self, progress: float) -> None:
        pass
    
    @abstractmethod
    def on_complete(self, result: ConversionResult) -> None:
        pass

class ProgressBarObserver(ConversionObserver):
    def on_progress(self, progress: float) -> None:
        # Update progress bar
        pass
```

## Data Flow

### CLI Processing Flow

```
User Input
    │
    ▼
┌─────────────────────┐
│ Argument Parsing    │ ← ArgumentParser.parse_args()
│ & Validation        │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ File Validation     │ ← FileValidator.validate_pdf_file()
│                     │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Output Path         │ ← FileValidator.validate_output_path()
│ Validation          │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ PDF Processing      │ ← PdfToMarkdownCli._process_pdf_file()
│ (Current: Stub)     │   (Future: Domain layer)
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Output Generation   │ ← Write to file system
│ & User Feedback     │
└─────────────────────┘
    │
    ▼
Exit Code
```

### Error Flow

```
Exception Occurred
    │
    ▼
┌─────────────────────┐
│ Exception Type      │
│ Classification      │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Error Message       │ ← OutputHandler.error()
│ Formatting          │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Logging (if debug)  │ ← Logger.exception()
│                     │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Exit Code           │ ← Specific exit code
│ Assignment          │   based on exception type
└─────────────────────┘
```

### Future PDF Processing Flow

```
PDF File Input
    │
    ▼
┌─────────────────────┐
│ PDF Parser          │ ← Infrastructure layer
│ (pdfminer.six)      │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Content Extraction  │ ← Domain layer
│ & Structure         │
│ Analysis            │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Conversion Pipeline │ ← Strategy pattern
│ - Headers           │   Multiple converters
│ - Paragraphs        │
│ - Tables            │
│ - Lists             │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Markdown Assembly   │ ← Domain service
│ & Formatting        │
└─────────────────────┘
    │
    ▼
Markdown Output
```

## Component Design

### ArgumentParser Component

```python
class ArgumentParser:
    """
    Responsibilities:
    - Parse command-line arguments
    - Validate argument constraints
    - Provide help and version information
    
    Dependencies:
    - ApplicationConfig (for defaults and limits)
    
    Design Patterns:
    - Factory pattern for creation
    - Value object for parsed arguments
    """
    
    def __init__(self, config: ApplicationConfig):
        self._config = config
        self._parser = self._create_parser()
    
    def parse_args(self, args: Optional[Sequence[str]] = None) -> CliArguments:
        # Parse and validate arguments
        pass
```

### FileValidator Component

```python
class FileValidator:
    """
    Responsibilities:
    - Validate PDF file existence and readability
    - Check file size limits
    - Validate output path permissions
    
    Business Rules:
    - PDF files must have .pdf extension
    - File size must not exceed configured limit
    - Output directory must be writable
    
    Design Patterns:
    - Result object for validation outcomes
    - Strategy pattern for different validation rules
    """
    
    def validate_pdf_file(self, file_path: Path) -> ValidationResult:
        # Implement validation business rules
        pass
```

### Configuration Management

```python
class ApplicationConfig:
    """
    Responsibilities:
    - Centralized configuration management
    - Environment variable support
    - Default value management
    
    Design Patterns:
    - Singleton pattern (via config_manager)
    - Builder pattern for configuration creation
    """
    
    @dataclass
    class ProcessingConfig:
        max_file_size_mb: int = 100
        timeout_seconds: int = 300
    
    @dataclass
    class LoggingConfig:
        level: str = "INFO"
        format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Error Handling Strategy

### Exception Hierarchy

```python
class PdfToMarkdownError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, context: Optional[Dict] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

class ValidationError(PdfToMarkdownError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field

class InvalidPdfError(PdfToMarkdownError):
    """Raised when PDF file is invalid or corrupted."""
    pass

class ProcessingError(PdfToMarkdownError):
    """Raised when PDF processing fails."""
    pass

class FileSystemError(PdfToMarkdownError):
    """Raised when file system operations fail."""
    
    def __init__(self, message: str, operation: str, file_path: str):
        super().__init__(message)
        self.operation = operation
        self.file_path = file_path
```

### Error Handling Patterns

1. **Fail Fast**: Validate inputs early and fail immediately
2. **Graceful Degradation**: Continue processing when possible
3. **Contextual Information**: Provide actionable error messages
4. **Logging**: Log errors with appropriate detail levels
5. **Recovery**: Suggest recovery actions when possible

## Configuration Management

### Configuration Sources (Priority Order)

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration files**
4. **Default values** (lowest priority)

### Configuration Structure

```python
@dataclass
class ApplicationConfig:
    app_name: str = "pdf2markdown"
    version: str = "1.0.0"
    debug: bool = False
    
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def from_environment(cls) -> 'ApplicationConfig':
        """Create configuration from environment variables."""
        pass
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'ApplicationConfig':
        """Create configuration from TOML file."""
        pass
```

### Environment Variable Mapping

```bash
PDF2MD_DEBUG=true              # ApplicationConfig.debug
PDF2MD_MAX_FILE_SIZE=200       # ProcessingConfig.max_file_size_mb
PDF2MD_LOG_LEVEL=DEBUG         # LoggingConfig.level
PDF2MD_LOG_FILE=/tmp/app.log   # LoggingConfig.log_file_path
```

## Testing Architecture

### Test Pyramid Strategy

```
         ┌─────────────────┐
         │   E2E Tests     │ 10% - Complete user scenarios
         │   (Slow)        │
         └─────────────────┘
       ┌───────────────────────┐
       │  Integration Tests    │ 20% - Component interaction
       │   (Medium)            │
       └───────────────────────┘
    ┌────────────────────────────────┐
    │        Unit Tests              │ 70% - Business logic
    │        (Fast)                  │
    └────────────────────────────────┘
```

### Test Organization

```
tests/
├── unit/                          # Fast, isolated unit tests
│   ├── test_argument_parser.py    # CLI argument parsing logic
│   ├── test_config.py             # Configuration management
│   ├── test_exceptions.py         # Exception behavior
│   ├── test_file_validator.py     # File validation business rules
│   └── test_main_module.py        # Module entry point
│
├── integration/                   # Component integration tests
│   ├── test_cli_integration.py    # Full CLI workflow
│   └── test_file_operations.py    # File system integration
│
└── e2e/                          # End-to-end scenarios
    ├── test_complete_conversion.py
    └── test_error_scenarios.py
```

### Test Patterns

```python
# Unit test example
class TestFileValidator:
    def test_valid_pdf_file_passes_validation(self, tmp_path):
        # Arrange
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        validator = FileValidator()
        
        # Act
        result = validator.validate_pdf_file(pdf_file)
        
        # Assert
        assert result.is_valid
        assert len(result.errors) == 0

# Integration test example
class TestCliIntegration:
    def test_successful_conversion_workflow(self, tmp_path):
        # Arrange
        input_file = tmp_path / "input.pdf"
        output_file = tmp_path / "output.md"
        input_file.write_bytes(create_valid_pdf())
        
        cli = PdfToMarkdownCli()
        args = [str(input_file), "--output", str(output_file)]
        
        # Act
        exit_code = cli.run(args)
        
        # Assert
        assert exit_code == 0
        assert output_file.exists()
        assert output_file.read_text().startswith("# Converted from")
```

## Performance Considerations

### Memory Management

1. **Streaming Processing**: Process large PDFs in chunks
2. **Lazy Loading**: Load content only when needed
3. **Resource Cleanup**: Explicit cleanup of temporary resources
4. **Memory Monitoring**: Track memory usage in debug mode

### CPU Optimization

1. **Algorithm Efficiency**: Use optimal algorithms for text processing
2. **Parallel Processing**: Support for concurrent processing (future)
3. **Caching**: Cache expensive operations (future)
4. **Profiling**: Built-in performance profiling in debug mode

### I/O Optimization

1. **Buffered Operations**: Use buffered I/O for file operations
2. **Batch Operations**: Minimize system calls
3. **Temporary Files**: Minimize temporary file usage
4. **Error Recovery**: Handle I/O errors gracefully

## Security Architecture

### Input Validation

1. **File Type Validation**: Strict PDF file type checking
2. **Path Sanitization**: Prevent directory traversal attacks
3. **Size Limits**: Enforce file size limits
4. **Permission Checks**: Validate file permissions

### Safe Processing

1. **Sandboxed Processing**: Isolate PDF processing operations
2. **Resource Limits**: Memory and CPU usage limits
3. **Timeout Handling**: Prevent infinite processing loops
4. **Error Containment**: Prevent information leakage

### Output Security

1. **Safe File Creation**: Secure temporary file handling
2. **Path Validation**: Validate output paths
3. **Content Sanitization**: Sanitize generated Markdown
4. **Atomic Operations**: Ensure atomic file operations

## Future Extensions

### Plugin Architecture

```python
# Future plugin interface
class ConversionPlugin(ABC):
    @abstractmethod
    def can_handle(self, content_type: str) -> bool:
        pass
    
    @abstractmethod
    def convert(self, content: Any) -> str:
        pass

class PluginManager:
    def __init__(self):
        self._plugins = []
    
    def register_plugin(self, plugin: ConversionPlugin):
        self._plugins.append(plugin)
    
    def get_converter(self, content_type: str) -> Optional[ConversionPlugin]:
        for plugin in self._plugins:
            if plugin.can_handle(content_type):
                return plugin
        return None
```

### Web Interface (v2+)

```python
# Future web API structure
class WebApiController:
    def __init__(self, conversion_service: ConversionService):
        self._service = conversion_service
    
    async def convert_pdf(self, request: ConversionRequest) -> ConversionResponse:
        # Web-based conversion endpoint
        pass
```

### Batch Processing

```python
# Future batch processing capability
class BatchProcessor:
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
    
    async def process_batch(self, files: List[Path]) -> List[ConversionResult]:
        # Parallel batch processing
        pass
```

### Advanced Features

1. **Table Recognition**: Advanced table parsing algorithms
2. **Image Extraction**: Extract and reference images
3. **OCR Integration**: Optional OCR for scanned PDFs
4. **Custom Templates**: User-defined output templates
5. **Format Support**: Additional output formats (HTML, reStructuredText)

---

This architecture provides a solid foundation for the current CLI implementation while enabling future enhancements and maintaining code quality, testability, and maintainability.