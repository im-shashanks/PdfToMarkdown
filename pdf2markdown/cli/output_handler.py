"""
Output handling and user feedback for PdfToMarkdown CLI.

This module provides enhanced terminal output with colors, progress indicators,
and consistent formatting using the rich library while following the
Single Responsibility Principle.
"""

import sys
from pathlib import Path
from typing import Any
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn
    from rich.progress import Progress
    from rich.progress import SpinnerColumn
    from rich.progress import TaskID
    from rich.progress import TextColumn
    from rich.progress import TimeRemainingColumn
    from rich.text import Text
    from rich.traceback import install as install_rich_traceback
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from pdf2markdown.core.config import ApplicationConfig


class OutputHandler:
    """Handles all CLI output and user feedback.
    
    This class provides a consistent interface for outputting messages,
    progress indicators, and error information with appropriate formatting
    and color coding.
    """

    def __init__(self, config: ApplicationConfig, use_rich: bool = True) -> None:
        """Initialize output handler.
        
        Args:
            config: Application configuration
            use_rich: Whether to use rich formatting (falls back to plain text)
        """
        self._config = config
        self._use_rich = use_rich and RICH_AVAILABLE

        if self._use_rich:
            self._console = Console(stderr=True)
            self._stdout_console = Console(file=sys.stdout)
            # Install rich traceback handler for better error formatting
            install_rich_traceback(show_locals=config.debug)
        else:
            self._console = None
            self._stdout_console = None

        self._current_progress: Optional[Progress] = None
        self._current_task: Optional[TaskID] = None

    def info(self, message: str, **kwargs: Any) -> None:
        """Output an informational message.
        
        Args:
            message: Message to display
            **kwargs: Additional formatting arguments
        """
        if self._use_rich:
            self._console.print(f"[blue]ℹ[/blue] {message}", **kwargs)
        else:
            print(f"INFO: {message}", file=sys.stderr)

    def success(self, message: str, **kwargs: Any) -> None:
        """Output a success message.
        
        Args:
            message: Success message to display
            **kwargs: Additional formatting arguments
        """
        if self._use_rich:
            self._console.print(f"[green]✓[/green] {message}", **kwargs)
        else:
            print(f"SUCCESS: {message}", file=sys.stderr)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Output a warning message.
        
        Args:
            message: Warning message to display
            **kwargs: Additional formatting arguments
        """
        if self._use_rich:
            self._console.print(f"[yellow]⚠[/yellow] {message}", **kwargs)
        else:
            print(f"WARNING: {message}", file=sys.stderr)

    def error(self, message: str, **kwargs: Any) -> None:
        """Output an error message.
        
        Args:
            message: Error message to display
            **kwargs: Additional formatting arguments
        """
        if self._use_rich:
            self._console.print(f"[red]✗[/red] {message}", **kwargs)
        else:
            print(f"ERROR: {message}", file=sys.stderr)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Output a debug message (only if debug mode is enabled).
        
        Args:
            message: Debug message to display
            **kwargs: Additional formatting arguments
        """
        if not self._config.debug:
            return

        if self._use_rich:
            self._console.print(f"[dim]🐛 DEBUG: {message}[/dim]", **kwargs)
        else:
            print(f"DEBUG: {message}", file=sys.stderr)

    def print_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Print a formatted header for the application.
        
        Args:
            title: Main title text
            subtitle: Optional subtitle text
        """
        if self._use_rich:
            header_text = f"[bold blue]{title}[/bold blue]"
            if subtitle:
                header_text += f"\n[dim]{subtitle}[/dim]"

            panel = Panel(
                header_text,
                border_style="blue",
                padding=(1, 2)
            )
            self._console.print(panel)
        else:
            print(f"=== {title} ===", file=sys.stderr)
            if subtitle:
                print(subtitle, file=sys.stderr)
            print("", file=sys.stderr)

    def print_file_info(self, file_path: Path, file_size: Optional[int] = None) -> None:
        """Print formatted file information.
        
        Args:
            file_path: Path to the file
            file_size: Optional file size in bytes
        """
        if self._use_rich:
            info_text = f"[bold]File:[/bold] {file_path}"
            if file_size is not None:
                size_mb = file_size / (1024 * 1024)
                info_text += f"\n[bold]Size:[/bold] {size_mb:.2f} MB ({file_size:,} bytes)"

            self._console.print(Panel(info_text, title="File Information", border_style="cyan"))
        else:
            print(f"File: {file_path}", file=sys.stderr)
            if file_size is not None:
                size_mb = file_size / (1024 * 1024)
                print(f"Size: {size_mb:.2f} MB ({file_size:,} bytes)", file=sys.stderr)

    def start_progress(self, description: str = "Processing...") -> Optional[TaskID]:
        """Start a progress indicator.
        
        Args:
            description: Description of the operation
            
        Returns:
            Task ID for updating progress (if rich is available)
        """
        if not self._use_rich:
            print(f"{description}", file=sys.stderr, end="", flush=True)
            return None

        if self._current_progress is not None:
            self.end_progress()

        self._current_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self._console
        )

        self._current_progress.start()
        self._current_task = self._current_progress.add_task(description, total=100)

        return self._current_task

    def update_progress(self, task_id: Optional[TaskID], advance: int = 1, description: Optional[str] = None) -> None:
        """Update progress indicator.
        
        Args:
            task_id: Task ID returned from start_progress
            advance: Amount to advance progress
            description: Optional new description
        """
        if not self._use_rich or self._current_progress is None or task_id is None:
            if not self._use_rich:
                print(".", file=sys.stderr, end="", flush=True)
            return

        if description:
            self._current_progress.update(task_id, advance=advance, description=description)
        else:
            self._current_progress.update(task_id, advance=advance)

    def end_progress(self, final_message: Optional[str] = None) -> None:
        """End the current progress indicator.
        
        Args:
            final_message: Optional final message to display
        """
        if self._current_progress is not None:
            self._current_progress.stop()
            self._current_progress = None
            self._current_task = None
        elif not self._use_rich:
            print(" done", file=sys.stderr)

        if final_message:
            self.success(final_message)

    def print_summary(self, input_file: Path, output_file: Path, processing_time: float) -> None:
        """Print a summary of the conversion operation.
        
        Args:
            input_file: Input PDF file path
            output_file: Output Markdown file path
            processing_time: Time taken for processing in seconds
        """
        if self._use_rich:
            summary_text = (
                f"[bold]Input:[/bold] {input_file}\n"
                f"[bold]Output:[/bold] {output_file}\n"
                f"[bold]Processing Time:[/bold] {processing_time:.2f} seconds"
            )

            panel = Panel(
                summary_text,
                title="[bold green]Conversion Summary[/bold green]",
                border_style="green"
            )
            self._console.print(panel)
        else:
            print("=== Conversion Summary ===", file=sys.stderr)
            print(f"Input: {input_file}", file=sys.stderr)
            print(f"Output: {output_file}", file=sys.stderr)
            print(f"Processing Time: {processing_time:.2f} seconds", file=sys.stderr)

    def print_validation_results(self, validation_result) -> None:
        """Print file validation results with appropriate formatting.
        
        Args:
            validation_result: FileValidationResult object
        """
        if validation_result.is_valid:
            self.success("File validation passed")
        else:
            self.error("File validation failed")

        # Print errors
        for error in validation_result.errors:
            self.error(f"  {error}")

        # Print warnings
        for warning in validation_result.warnings:
            self.warning(f"  {warning}")

        # Print file info if available
        if validation_result.file_size is not None:
            size_mb = validation_result.file_size / (1024 * 1024)
            self.debug(f"File size: {size_mb:.2f} MB")

        if validation_result.mime_type:
            self.debug(f"MIME type: {validation_result.mime_type}")

    def output(self, content: str) -> None:
        """Output content to stdout (for piping and redirection).
        
        Args:
            content: Content to output
        """
        if self._use_rich and self._stdout_console:
            self._stdout_console.print(content, end="")
        else:
            print(content, end="")


class PlainOutputHandler(OutputHandler):
    """Plain text output handler without rich formatting.
    
    This handler provides a fallback for environments where rich
    is not available or desired.
    """

    def __init__(self, config: ApplicationConfig) -> None:
        """Initialize plain output handler.
        
        Args:
            config: Application configuration
        """
        super().__init__(config, use_rich=False)


def create_output_handler(config: ApplicationConfig, force_plain: bool = False) -> OutputHandler:
    """Factory function to create appropriate output handler.
    
    Args:
        config: Application configuration
        force_plain: Force plain text output even if rich is available
        
    Returns:
        Configured OutputHandler instance
    """
    if force_plain or not RICH_AVAILABLE:
        return PlainOutputHandler(config)
    else:
        return OutputHandler(config)
