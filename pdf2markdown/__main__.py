"""
Entry point for running pdf2markdown as a module.

This module enables the package to be executed as:
    python -m pdf2markdown

It serves as the main entry point when the package is invoked directly,
providing a clean interface to the CLI functionality.
"""

import sys

from pdf2markdown.cli.main import PdfToMarkdownCli


def main() -> None:
    """Main entry point for module execution.
    
    Creates a CLI instance and runs it with command-line arguments,
    then exits with the appropriate status code.
    """
    cli = PdfToMarkdownCli()
    exit_code = cli.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()