# Contributing to PdfToMarkdown

Thank you for your interest in contributing to PdfToMarkdown! This document provides guidelines and information for contributors to help maintain code quality and ensure a smooth development experience.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Architecture Guidelines](#architecture-guidelines)
- [Performance Guidelines](#performance-guidelines)

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct:

- **Be respectful**: Treat all community members with respect and kindness
- **Be inclusive**: Welcome contributors from all backgrounds and experience levels
- **Be constructive**: Provide helpful feedback and suggestions
- **Be patient**: Remember that everyone is learning and improving
- **Focus on the code**: Keep discussions technical and objective

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip or poetry package manager

### Development Setup

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/PdfToMarkdown.git
   cd PdfToMarkdown
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Verify Setup**
   ```bash
   # Run tests to ensure everything is working
   pytest
   
   # Run linting
   ruff check .
   
   # Run type checking
   mypy .
   ```

### Project Structure

Understanding the project architecture is crucial for effective contributions:

```
pdf2markdown/
├── cli/                 # Command-line interface layer
│   ├── argument_parser.py   # CLI argument parsing
│   ├── main.py             # Main CLI application
│   └── output_handler.py   # User output formatting
├── core/                # Core business logic
│   ├── config.py           # Configuration management
│   ├── exceptions.py       # Custom exceptions
│   └── file_validator.py   # File validation
├── domain/              # Domain models (future)
└── infrastructure/      # External services (future)

tests/
├── unit/               # Unit tests
└── integration/        # Integration tests

docs/                   # Documentation
├── api.md             # API documentation
└── architecture/      # Architecture documentation
```

## Development Workflow

### Branch Strategy

- **main**: Production-ready code
- **feature/\***: New features (`feature/add-table-parsing`)
- **bugfix/\***: Bug fixes (`bugfix/fix-cli-parsing`)
- **docs/\***: Documentation updates (`docs/update-api`)

### Workflow Steps

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our standards
   - Add/update tests
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   # Run all tests
   pytest
   
   # Check coverage
   pytest --cov=pdf2markdown --cov-report=html
   
   # Run quality checks
   ruff check .
   black --check .
   mypy .
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add table parsing functionality"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

## Code Standards

### Clean Architecture Principles

PdfToMarkdown follows clean architecture principles. Please ensure your contributions align with these patterns:

#### SOLID Principles

1. **Single Responsibility Principle (SRP)**
   - Each class should have one reason to change
   - Separate concerns clearly (parsing, validation, output)

2. **Open/Closed Principle (OCP)**
   - Open for extension, closed for modification
   - Use interfaces and dependency injection

3. **Liskov Substitution Principle (LSP)**
   - Subtypes must be substitutable for their base types
   - Maintain behavioral contracts

4. **Interface Segregation Principle (ISP)**
   - Clients shouldn't depend on interfaces they don't use
   - Create focused, specific interfaces

5. **Dependency Inversion Principle (DIP)**
   - Depend on abstractions, not concretions
   - Use dependency injection

#### Code Organization

```python
# Good: Clear separation of concerns
class PdfValidator:
    """Validates PDF files according to business rules."""
    
    def validate_pdf_file(self, file_path: Path) -> ValidationResult:
        """Validate a PDF file."""
        pass

class MarkdownGenerator:
    """Generates Markdown from parsed PDF content."""
    
    def generate_markdown(self, pdf_content: PdfContent) -> str:
        """Generate Markdown from PDF content."""
        pass

# Bad: Mixed responsibilities
class PdfProcessor:
    """Processes PDFs (validation + parsing + generation)."""
    pass
```

### Coding Style

#### Python Code Style

We use strict linting and formatting tools:

- **Black**: Code formatting (line length: 88)
- **Ruff**: Linting with comprehensive rule set
- **MyPy**: Static type checking with strict mode

#### Type Hints

All public APIs must include type hints:

```python
from typing import Optional, List, Dict, Any
from pathlib import Path

def process_pdf(
    input_file: Path,
    output_file: Optional[Path] = None,
    options: Dict[str, Any] = None
) -> bool:
    """Process a PDF file with type safety."""
    pass
```

#### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def validate_pdf_file(self, file_path: Path) -> ValidationResult:
    """Validate a PDF file for processing.
    
    Args:
        file_path: Path to the PDF file to validate
        
    Returns:
        ValidationResult containing validation status and any warnings
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValidationError: If the file is not a valid PDF
        
    Example:
        >>> validator = PdfValidator()
        >>> result = validator.validate_pdf_file(Path("document.pdf"))
        >>> if result.is_valid:
        ...     print("PDF is valid")
    """
```

#### Error Handling

Use custom exceptions with clear error messages:

```python
# Good: Specific, actionable error
raise InvalidPdfError(
    f"PDF file is password-protected: {file_path}",
    file_path=file_path,
    error_code="PASSWORD_PROTECTED"
)

# Bad: Generic error
raise Exception("Bad PDF")
```

#### Logging

Use structured logging with appropriate levels:

```python
import logging

logger = logging.getLogger(__name__)

def process_pdf(file_path: Path) -> None:
    logger.info(f"Processing PDF: {file_path}")
    
    try:
        # Processing logic
        logger.debug(f"Extracted {page_count} pages")
    except Exception as e:
        logger.error(f"Failed to process PDF: {e}", exc_info=True)
        raise
    
    logger.info(f"Successfully processed PDF: {file_path}")
```

## Testing

### Test Strategy

We follow the test pyramid with comprehensive coverage:

- **Unit Tests (70%)**: Fast, isolated tests for business logic
- **Integration Tests (20%)**: Component integration and API contracts
- **End-to-End Tests (10%)**: Complete user workflows

### Test Structure

```python
import pytest
from pathlib import Path
from pdf2markdown.core.file_validator import FileValidator

class TestFileValidator:
    """Test cases for FileValidator class."""
    
    def test_validate_valid_pdf_file(self, tmp_path: Path) -> None:
        """Test validation of a valid PDF file."""
        # Arrange
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")  # Minimal PDF header
        validator = FileValidator()
        
        # Act
        result = validator.validate_pdf_file(pdf_file)
        
        # Assert
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_nonexistent_file(self) -> None:
        """Test validation of non-existent file."""
        # Arrange
        validator = FileValidator()
        nonexistent_file = Path("does_not_exist.pdf")
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            validator.validate_pdf_file(nonexistent_file)
```

### Testing Guidelines

1. **Test Naming**: Use descriptive test names that explain the scenario
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Test Isolation**: Each test should be independent and atomic
4. **Test Data**: Use fixtures and temporary files for test data
5. **Mock External Dependencies**: Mock file system, network calls, etc.

### Running Tests

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with coverage
pytest --cov=pdf2markdown --cov-report=html

# Run tests in parallel
pytest -n auto

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_file_validator.py

# Run specific test method
pytest tests/unit/test_file_validator.py::test_validate_valid_pdf_file
```

## Pull Request Process

### Before Submitting

1. **Ensure Quality Gates Pass**
   ```bash
   # All tests pass
   pytest
   
   # Code coverage > 90%
   pytest --cov=pdf2markdown --cov-fail-under=90
   
   # Linting passes
   ruff check .
   
   # Formatting is correct
   black --check .
   
   # Type checking passes
   mypy .
   ```

2. **Update Documentation**
   - Update API documentation if needed
   - Add examples for new features
   - Update README if necessary

3. **Add Tests**
   - Unit tests for new functionality
   - Integration tests for API changes
   - Maintain or improve coverage

### PR Guidelines

#### Title Format

Use conventional commit format:

- `feat: add table parsing support`
- `fix: resolve CLI argument parsing issue`
- `docs: update API documentation`
- `test: add integration tests for CLI`
- `refactor: improve error handling architecture`

#### Description Template

```markdown
## Summary
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Coverage maintained or improved

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

### Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: All tests must pass with appropriate coverage
4. **Documentation**: Documentation must be updated for user-facing changes

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Describe the Bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command: `pdf2md example.pdf`
2. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.0]
- PdfToMarkdown Version: [e.g., 1.0.0]

**Additional Context**
Add any other context about the problem here.
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
Describe how you envision this feature working.

**Alternatives Considered**
Any alternative solutions you've considered.

**Additional Context**
Any additional context or screenshots.
```

## Architecture Guidelines

### Adding New Features

When adding new features, follow these architectural principles:

1. **Domain-Driven Design**
   - Place business logic in the domain layer
   - Keep infrastructure concerns separate
   - Use value objects for data without identity

2. **Dependency Injection**
   - Inject dependencies through constructors
   - Use factory functions for complex object creation
   - Avoid global state and singletons

3. **Error Handling**
   - Use custom exceptions with specific error types
   - Provide actionable error messages
   - Log errors with appropriate context

4. **Configuration**
   - Use configuration objects for settings
   - Support environment variable overrides
   - Validate configuration at startup

### Example: Adding a New Converter

```python
# 1. Define domain interface
from abc import ABC, abstractmethod

class ContentConverter(ABC):
    """Abstract interface for content conversion."""
    
    @abstractmethod
    def convert(self, content: str) -> str:
        """Convert content to target format."""
        pass

# 2. Implement concrete converter
class TableConverter(ContentConverter):
    """Converts PDF table content to Markdown tables."""
    
    def __init__(self, config: TableConfig) -> None:
        self._config = config
    
    def convert(self, content: str) -> str:
        """Convert table content to Markdown format."""
        # Implementation here
        pass

# 3. Add factory function
def create_table_converter(config: ApplicationConfig) -> TableConverter:
    """Create table converter with proper configuration."""
    table_config = TableConfig(
        max_columns=config.table.max_columns,
        column_separator=config.table.separator
    )
    return TableConverter(table_config)

# 4. Integration in main application
class PdfProcessor:
    def __init__(self, converters: List[ContentConverter]) -> None:
        self._converters = converters
    
    def process(self, pdf_content: PdfContent) -> str:
        result = pdf_content.raw_text
        
        for converter in self._converters:
            result = converter.convert(result)
        
        return result
```

## Performance Guidelines

### Performance Requirements

- **CLI Response Time**: < 1 second for typical 5-page PDFs
- **Memory Usage**: < 100MB for 50-page documents
- **CPU Usage**: Efficient single-threaded processing
- **File I/O**: Minimize disk operations

### Performance Best Practices

1. **Memory Efficiency**
   ```python
   # Good: Process in chunks
   def process_large_pdf(file_path: Path) -> Iterator[str]:
       with open(file_path, 'rb') as f:
           while chunk := f.read(8192):
               yield process_chunk(chunk)
   
   # Bad: Load entire file in memory
   def process_large_pdf(file_path: Path) -> str:
       with open(file_path, 'rb') as f:
           content = f.read()  # Loads entire file
           return process_content(content)
   ```

2. **Algorithm Efficiency**
   ```python
   # Good: O(n) complexity
   def find_headers(lines: List[str]) -> List[Header]:
       headers = []
       for line in lines:
           if is_header(line):
               headers.append(parse_header(line))
       return headers
   
   # Bad: O(n²) complexity
   def find_headers(lines: List[str]) -> List[Header]:
       headers = []
       for i, line in enumerate(lines):
           if is_header(line):
               # Expensive operation for each line
               context = analyze_surrounding_lines(lines, i)
               headers.append(parse_header(line, context))
       return headers
   ```

3. **I/O Optimization**
   ```python
   # Good: Batch file operations
   def write_output_files(results: Dict[str, str]) -> None:
       for filename, content in results.items():
           with open(filename, 'w') as f:
               f.write(content)
   
   # Bad: Multiple open/close cycles
   def write_output_files(results: Dict[str, str]) -> None:
       for filename, content in results.items():
           f = open(filename, 'w')
           f.write(content)
           f.close()
   ```

## Getting Help

### Resources

- **Documentation**: [API Documentation](docs/api.md)
- **Architecture**: [Architecture Documentation](docs/architecture/)
- **Examples**: [Example Scripts](examples/)
- **Issues**: [GitHub Issues](https://github.com/im-shashanks/PdfToMarkdown/issues)

### Community

- **Discussions**: Use GitHub Discussions for questions and ideas
- **Issues**: Use GitHub Issues for bugs and feature requests
- **Reviews**: Participate in code reviews to learn and contribute

### Mentorship

New contributors are welcome! If you're new to open source or need guidance:

1. Look for issues labeled `good first issue`
2. Ask questions in GitHub Discussions
3. Request review and feedback on your PRs
4. Pair with experienced contributors when possible

## Recognition

Contributors are recognized in several ways:

- **Contributors List**: All contributors are listed in the README
- **Release Notes**: Significant contributions are highlighted in releases
- **Documentation**: Contributors are credited in relevant documentation

Thank you for contributing to PdfToMarkdown! Your efforts help make document processing more accessible and efficient for the developer community.

---

*Last updated: July 2025*