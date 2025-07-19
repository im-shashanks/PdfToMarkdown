# CLI Interface Documentation

This document provides comprehensive documentation for the PdfToMarkdown command-line interface, including all options, examples, and advanced usage patterns.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Command Syntax](#command-syntax)
- [Arguments and Options](#arguments-and-options)
- [Exit Codes](#exit-codes)
- [Usage Examples](#usage-examples)
- [Advanced Usage](#advanced-usage)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)
- [Troubleshooting](#troubleshooting)

## Quick Reference

```bash
# Basic conversion
pdf2md document.pdf

# Specify output file
pdf2md document.pdf --output converted.md

# Overwrite existing files
pdf2md document.pdf --force

# Verbose output
pdf2md document.pdf --verbose

# Debug mode
pdf2md document.pdf --debug

# Quiet mode (errors only)
pdf2md document.pdf --quiet

# Show help
pdf2md --help

# Show version
pdf2md --version
```

## Command Syntax

```bash
pdf2md <input_file> [OPTIONS]
```

### Basic Structure

- **Command**: `pdf2md` (or `python -m pdf2markdown`)
- **Input File**: Required positional argument (PDF file path)
- **Options**: Optional flags and parameters

## Arguments and Options

### Positional Arguments

#### `input_file` (Required)

Path to the PDF file to convert.

**Requirements:**
- Must exist and be readable
- Must have `.pdf` extension (case-insensitive)
- Must be a regular file (not a directory or special file)
- File size must not exceed configured limit (default: 100MB)

**Examples:**
```bash
pdf2md document.pdf
pdf2md /path/to/report.pdf
pdf2md ./files/presentation.PDF
pdf2md "file with spaces.pdf"
```

**Error Cases:**
- File doesn't exist: `File not found: missing.pdf`
- Wrong extension: `File must have .pdf extension: document.txt`
- Too large: `File size exceeds 100MB limit: huge.pdf`
- Not readable: `File is not readable: protected.pdf`

### Optional Arguments

#### `-o, --output <path>`

Specify the output Markdown file path.

**Default Behavior:**
- If not specified, uses input filename with `.md` extension
- Output file is created in the same directory as input file

**Path Handling:**
- Supports absolute and relative paths
- Creates parent directories if they don't exist (with appropriate permissions)
- Resolves symbolic links and path components

**Examples:**
```bash
# Default output (document.md)
pdf2md document.pdf

# Custom output filename
pdf2md document.pdf --output report.md

# Output to different directory
pdf2md document.pdf --output /home/user/docs/converted.md

# Output with spaces (quoted)
pdf2md document.pdf --output "My Document.md"

# Relative path
pdf2md document.pdf --output ../converted/report.md
```

#### `-f, --force`

Overwrite existing output files without confirmation.

**Default Behavior:**
- Without `--force`: Error if output file already exists
- With `--force`: Silently overwrites existing files

**Examples:**
```bash
# Will error if output.md exists
pdf2md document.pdf --output output.md

# Will overwrite output.md if it exists
pdf2md document.pdf --output output.md --force

# Combine with other options
pdf2md document.pdf --force --verbose
```

#### `-v, --verbose`

Enable verbose output with progress and status information.

**Output Includes:**
- Processing start/completion messages
- File validation results
- Conversion progress indicators
- Performance metrics
- Warning messages

**Log Level:** INFO and above

**Examples:**
```bash
pdf2md document.pdf --verbose
```

**Sample Output:**
```
Starting pdf2markdown v1.0.0
Processing document.pdf...
✓ PDF validation passed
⚠ Warning: Large file may take longer to process
Converting pages: [████████████████████████████████] 100%
✓ Successfully converted document.pdf to document.md
Conversion completed in 0.85 seconds
```

#### `-d, --debug`

Enable debug mode with maximum detail and verbose output.

**Output Includes:**
- All verbose output
- Internal processing details
- Performance profiling
- Exception stack traces
- Configuration values
- Detailed parsing information

**Log Level:** DEBUG and above

**Note:** Debug mode automatically enables verbose mode

**Examples:**
```bash
pdf2md document.pdf --debug
```

**Sample Output:**
```
Starting pdf2markdown v1.0.0
DEBUG: Configuration loaded from default settings
DEBUG: CLI arguments: {'input_file': 'document.pdf', 'verbose': True, 'debug': True}
Processing document.pdf...
DEBUG: PDF file size: 2.5 MB
DEBUG: PDF version: 1.4
DEBUG: Number of pages: 15
✓ PDF validation passed
DEBUG: Initializing PDF parser with pdfminer.six
DEBUG: Parsing page 1/15...
[... detailed processing information ...]
✓ Successfully converted document.pdf to document.md
DEBUG: Total processing time: 0.853 seconds
DEBUG: Memory usage: 45.2 MB peak
```

#### `-q, --quiet`

Suppress all output except errors.

**Output Includes:**
- Only error messages and critical warnings
- No progress indicators
- No success messages

**Log Level:** ERROR and above

**Conflict:** Cannot be used with `--verbose` or `--debug`

**Examples:**
```bash
pdf2md document.pdf --quiet
```

**Sample Output (success):**
```
(no output)
```

**Sample Output (error):**
```
Error: Invalid PDF: document.pdf is corrupted
```

#### `--version`

Show version information and exit.

**Output Format:**
```
pdf2md 1.0.0
```

**Examples:**
```bash
pdf2md --version
```

#### `-h, --help`

Show help message and exit.

**Output Includes:**
- Command syntax
- Description of all options
- Usage examples
- Exit codes

**Examples:**
```bash
pdf2md --help
pdf2md -h
```

## Exit Codes

The CLI uses standardized exit codes to indicate operation results:

| Code | Name | Description | Common Causes |
|------|------|-------------|---------------|
| `0` | SUCCESS | Operation completed successfully | PDF converted without errors |
| `1` | GENERAL_ERROR | General application error | Unexpected application issues |
| `2` | VALIDATION_ERROR | Input validation failed | Invalid file, bad arguments |
| `3` | OUTPUT_ERROR | Output path error | Cannot write output, permission denied |
| `4` | INVALID_PDF | Invalid PDF file | Corrupted PDF, password-protected |
| `5` | PROCESSING_ERROR | PDF processing failed | Parsing errors, unsupported features |
| `6` | FILESYSTEM_ERROR | File system operation failed | Disk full, I/O errors |
| `7` | CONFIGURATION_ERROR | Configuration error | Invalid settings, missing dependencies |
| `99` | UNEXPECTED_ERROR | Unexpected system error | Unhandled exceptions |
| `130` | INTERRUPTED | Operation interrupted by user | Ctrl+C pressed |

### Exit Code Usage in Scripts

```bash
#!/bin/bash

pdf2md document.pdf --quiet
exit_code=$?

case $exit_code in
    0)
        echo "✓ Conversion successful"
        ;;
    2)
        echo "✗ Invalid input file"
        ;;
    4)
        echo "✗ PDF file is corrupted or protected"
        ;;
    130)
        echo "✗ Operation cancelled by user"
        ;;
    *)
        echo "✗ Conversion failed (exit code: $exit_code)"
        ;;
esac

exit $exit_code
```

## Usage Examples

### Basic Conversion

```bash
# Convert PDF to Markdown (creates document.md)
pdf2md document.pdf

# Convert with custom output name
pdf2md report.pdf --output converted-report.md

# Convert file with spaces in name
pdf2md "Project Proposal.pdf"
```

### Directory Operations

```bash
# Convert to different directory
pdf2md document.pdf --output /home/user/markdown/document.md

# Convert to current directory from subdirectory
pdf2md ./pdfs/document.pdf --output document.md

# Convert with relative paths
pdf2md ../input/document.pdf --output ../output/document.md
```

### Batch Processing

```bash
# Convert all PDFs in current directory
for pdf in *.pdf; do
    echo "Converting $pdf..."
    pdf2md "$pdf" --quiet
done

# Convert with error handling
for pdf in *.pdf; do
    if pdf2md "$pdf" --quiet; then
        echo "✓ $pdf"
    else
        echo "✗ $pdf (failed)"
    fi
done

# Convert to specific output directory
mkdir -p converted
for pdf in *.pdf; do
    pdf2md "$pdf" --output "converted/${pdf%.pdf}.md" --force
done
```

### Advanced Batch Script

```bash
#!/bin/bash
# batch_convert.sh - Convert multiple PDFs with logging

INPUT_DIR="./pdfs"
OUTPUT_DIR="./markdown"
LOG_FILE="conversion.log"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Initialize log
echo "Batch conversion started at $(date)" > "$LOG_FILE"

success_count=0
error_count=0

for pdf in "$INPUT_DIR"/*.pdf; do
    if [ ! -f "$pdf" ]; then
        echo "No PDF files found in $INPUT_DIR"
        break
    fi
    
    filename=$(basename "$pdf" .pdf)
    output="$OUTPUT_DIR/$filename.md"
    
    echo "Converting $(basename "$pdf")..." | tee -a "$LOG_FILE"
    
    if pdf2md "$pdf" --output "$output" --force --quiet; then
        echo "✓ Success: $filename" | tee -a "$LOG_FILE"
        ((success_count++))
    else
        exit_code=$?
        echo "✗ Failed: $filename (exit code: $exit_code)" | tee -a "$LOG_FILE"
        ((error_count++))
    fi
done

echo "Conversion completed: $success_count success, $error_count errors" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE"
```

### Integration with Other Tools

```bash
# Pipe output to other tools (using --quiet to avoid extra output)
pdf2md document.pdf --quiet && echo "Conversion completed"

# Use in Makefile
convert-docs: $(PDF_FILES)
	@for pdf in $(PDF_FILES); do \
		pdf2md "$$pdf" --output "docs/$$(basename $$pdf .pdf).md" --force; \
	done

# Use with find
find ./documents -name "*.pdf" -exec pdf2md {} --force \;

# Use with parallel processing (GNU parallel)
find ./documents -name "*.pdf" | parallel pdf2md {} --force --quiet
```

## Advanced Usage

### Environment Variables

The CLI respects several environment variables for configuration:

```bash
# Set default output directory
export PDF2MD_OUTPUT_DIR="/home/user/markdown"

# Set default log level
export PDF2MD_LOG_LEVEL="DEBUG"

# Set maximum file size (MB)
export PDF2MD_MAX_FILE_SIZE="200"

# Examples using environment variables
PDF2MD_LOG_LEVEL=DEBUG pdf2md document.pdf
PDF2MD_MAX_FILE_SIZE=50 pdf2md large-document.pdf
```

### Configuration Files

The CLI can use configuration files for default settings:

```bash
# Use custom config file
pdf2md document.pdf --config custom-config.toml

# Example config file (pdf2md.toml)
[processing]
max_file_size_mb = 200
timeout_seconds = 300

[output]
default_format = "markdown"
include_metadata = true

[logging]
level = "INFO"
file_path = "pdf2md.log"
```

### Module Usage

Run as Python module for better integration:

```bash
# Direct module execution
python -m pdf2markdown document.pdf

# With custom Python path
PYTHONPATH=/custom/path python -m pdf2markdown document.pdf

# Using different Python version
python3.11 -m pdf2markdown document.pdf
```

### Docker Usage

```bash
# Using Docker container
docker run --rm -v $(pwd):/workspace pdf2markdown pdf2md /workspace/document.pdf

# With custom output directory
docker run --rm -v $(pwd):/input -v /output:/output pdf2markdown \
    pdf2md /input/document.pdf --output /output/document.md
```

## Error Handling

### Common Error Scenarios

#### File Not Found
```bash
$ pdf2md missing.pdf
Error: File not found: missing.pdf
$ echo $?
2
```

#### Invalid File Type
```bash
$ pdf2md document.txt
Error: File must have .pdf extension: document.txt
$ echo $?
2
```

#### Permission Denied
```bash
$ pdf2md protected.pdf
Error: File is not readable: protected.pdf
$ echo $?
2
```

#### Output File Exists
```bash
$ pdf2md document.pdf --output existing.md
Error: Output file already exists: existing.md (use --force to overwrite)
$ echo $?
3
```

#### Corrupted PDF
```bash
$ pdf2md corrupted.pdf
Error: Invalid PDF: corrupted.pdf is not a valid PDF file
$ echo $?
4
```

### Error Recovery Strategies

```bash
# Retry with force if output exists
pdf2md document.pdf --output report.md || \
pdf2md document.pdf --output report.md --force

# Fallback to different output location
pdf2md document.pdf --output /preferred/location.md || \
pdf2md document.pdf --output ./fallback.md

# Skip problematic files in batch processing
for pdf in *.pdf; do
    if ! pdf2md "$pdf" --quiet; then
        echo "Skipping problematic file: $pdf"
        continue
    fi
done
```

## Performance Tips

### Optimizing for Speed

```bash
# Use quiet mode for batch processing (reduces I/O)
pdf2md document.pdf --quiet

# Process files in parallel (GNU parallel)
ls *.pdf | parallel pdf2md {} --quiet

# Use local storage for temporary files
TMPDIR=/tmp pdf2md large-document.pdf
```

### Memory Management

```bash
# For very large files, monitor memory usage
time pdf2md large-document.pdf --debug

# Process large batches in chunks
find . -name "*.pdf" | head -10 | xargs -I {} pdf2md {} --force
```

### Disk Space Considerations

```bash
# Check available space before conversion
df -h . && pdf2md document.pdf

# Clean up temporary files
pdf2md document.pdf && rm -f /tmp/pdf2md-*
```

## Troubleshooting

### Debug Information

Enable debug mode to get detailed information:

```bash
pdf2md problematic.pdf --debug > debug.log 2>&1
```

### Common Issues and Solutions

#### "Command not found"
```bash
# Check if installed
pip list | grep pdf2markdown

# Reinstall if necessary
pip install --force-reinstall pdf2markdown

# Check PATH
which pdf2md
echo $PATH
```

#### Slow Performance
```bash
# Check file size
ls -lh document.pdf

# Monitor resource usage
top -p $(pgrep pdf2md)

# Use debug mode to identify bottlenecks
pdf2md document.pdf --debug
```

#### Memory Issues
```bash
# Check available memory
free -h

# Monitor memory usage during conversion
pdf2md document.pdf --debug &
PID=$!
while kill -0 $PID 2>/dev/null; do
    ps -o pid,vsz,rss,comm $PID
    sleep 1
done
```

#### Permission Issues
```bash
# Check file permissions
ls -la document.pdf

# Check output directory permissions
ls -la $(dirname output.md)

# Fix permissions if needed
chmod 644 document.pdf
chmod 755 $(dirname output.md)
```

### Getting Help

1. **Check the help text**: `pdf2md --help`
2. **Enable debug logging**: `pdf2md document.pdf --debug`
3. **Check the documentation**: [API Documentation](docs/api.md)
4. **Report issues**: [GitHub Issues](https://github.com/im-shashanks/PdfToMarkdown/issues)

### Reporting Bugs

When reporting issues, include:

1. **Command used**: Full command line with options
2. **Error output**: Complete error message
3. **Environment**: OS, Python version, pdf2markdown version
4. **File information**: PDF file size, version, source
5. **Debug log**: Output from `--debug` mode (if relevant)

```bash
# Collect debugging information
echo "pdf2markdown version:" && pdf2md --version
echo "Python version:" && python --version
echo "OS information:" && uname -a
echo "Command output:" && pdf2md document.pdf --debug
```

---

*For more detailed API information, see [API Documentation](docs/api.md)*  
*For architecture details, see [Architecture Documentation](ARCHITECTURE.md)*