"""
Code detection service for identifying monospace text and code blocks.

Follows Clean Architecture principles with dependency inversion.
"""

import re
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

from pdf2markdown.domain.interfaces.code_detector import CodeDetectorInterface
from pdf2markdown.domain.models.document import CodeBlock
from pdf2markdown.domain.models.document import CodeLanguage
from pdf2markdown.domain.models.document import CodeStyle
from pdf2markdown.domain.models.document import InlineCode
from pdf2markdown.domain.models.document import Line


@dataclass
class CodeDetectorConfig:
    """Configuration for code detection behavior."""
    monospace_fonts: Set[str]
    max_inline_code_length: int = 50
    character_width_threshold: float = 0.1
    min_code_block_lines: int = 1
    max_header_font_size: float = 14.0


class CodeDetector(CodeDetectorInterface):
    """
    Service for detecting code blocks and inline code in PDF content.
    
    Follows Single Responsibility Principle - only responsible for code detection.
    """

    # Default monospace font patterns
    DEFAULT_MONOSPACE_FONTS = {
        'courier', 'courier new', 'monaco', 'menlo',
        'consolas', 'inconsolata', 'source code pro', 'fira code',
        'fira mono', 'liberation mono', 'dejavu sans mono',
        'ubuntu mono', 'roboto mono', 'sf mono'
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize CodeDetector with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            config = {}

        # Set up configuration with defaults
        custom_fonts = set(font.lower() for font in config.get('monospace_fonts', []))
        all_fonts = self.DEFAULT_MONOSPACE_FONTS.union(custom_fonts)

        self.config = CodeDetectorConfig(
            monospace_fonts=all_fonts,
            max_inline_code_length=config.get('max_inline_code_length', 50),
            character_width_threshold=config.get('character_width_threshold', 0.1),
            min_code_block_lines=config.get('min_code_block_lines', 1),
            max_header_font_size=config.get('max_header_font_size', 14.0)
        )

        # Pre-compile regex patterns for performance
        self._font_patterns = [
            re.compile(rf'\b{re.escape(font)}\b', re.IGNORECASE)
            for font in self.config.monospace_fonts
        ]

    def is_monospace_font(self, font_family: str) -> bool:
        """
        Check if a font family is monospace.
        
        Args:
            font_family: Name of the font family to check
            
        Returns:
            True if the font is monospace, False otherwise
        """
        if not font_family:
            return False

        font_lower = font_family.lower().strip()

        # Direct lookup first for performance
        if font_lower in self.config.monospace_fonts:
            return True

        # Pattern matching for partial names like "Courier-Bold"
        return any(pattern.search(font_family) for pattern in self._font_patterns)

    def analyze_font_characteristics(self, lines: List[Line]) -> bool:
        """
        Analyze font characteristics to determine if text uses monospace fonts.
        
        Args:
            lines: List of lines to analyze
            
        Returns:
            True if lines appear to use consistent monospace characteristics
        """
        if not lines:
            return False

        monospace_lines = 0
        total_lines = len(lines)

        for line in lines:
            # Check if line has font family information
            font_family = getattr(line, '_font_family', '')
            if self.is_monospace_font(font_family):
                monospace_lines += 1

        # Consider it monospace if majority of lines use monospace fonts
        threshold = 0.7  # 70% of lines should be monospace
        return (monospace_lines / total_lines) >= threshold

    def detect_code_blocks(self, lines: List[Line]) -> List[CodeBlock]:
        """
        Detect code blocks from a list of lines.
        
        Args:
            lines: List of lines to analyze for code blocks
            
        Returns:
            List of detected code blocks
        """
        if not lines:
            return []

        code_blocks = []
        current_block_lines = []
        current_style = None

        for i, line in enumerate(lines):
            font_family = getattr(line, '_font_family', '')

            if self.is_monospace_font(font_family) and self.is_code_context(lines, i):
                # Add line to current code block
                current_block_lines.append(line)

                # Update or set style information (use the most indented line to get better style info)
                if current_style is None:
                    current_style = self._extract_code_style(line, font_family)
                else:
                    # Update style with more indented line if found
                    line_style = self._extract_code_style(line, font_family)
                    if line_style.indentation_level > current_style.indentation_level:
                        current_style = line_style
            # End of code block - save if it has content
            elif current_block_lines:
                code_block = CodeBlock(
                    lines=current_block_lines.copy(),
                    language=CodeLanguage.UNKNOWN,  # Language detection happens separately
                    style=current_style
                )
                if not code_block.is_empty():
                    code_blocks.append(code_block)

                # Reset for next block
                current_block_lines = []
                current_style = None

        # Handle final block if exists
        if current_block_lines:
            code_block = CodeBlock(
                lines=current_block_lines,
                language=CodeLanguage.UNKNOWN,
                style=current_style
            )
            if not code_block.is_empty():
                code_blocks.append(code_block)

        return code_blocks

    def detect_inline_code(self, line: Line) -> List[InlineCode]:
        """
        Detect inline code snippets within a single line.
        
        Args:
            line: Line to analyze for inline code
            
        Returns:
            List of detected inline code snippets
        """
        inline_codes = []

        # Check if line has font segment information
        font_segments = getattr(line, '_font_segments', [])
        if not font_segments:
            return inline_codes

        for segment in font_segments:
            font_family = segment.get('font_family', '')
            text = segment.get('text', '')

            # Check if segment is monospace and appropriate length for inline code
            if (self.is_monospace_font(font_family) and
                0 < len(text.strip()) <= self.config.max_inline_code_length):

                inline_code = InlineCode(
                    content=text,
                    font_family=font_family,
                    start_position=segment.get('start', 0.0),
                    end_position=segment.get('end', 0.0)
                )
                inline_codes.append(inline_code)

        return inline_codes

    def is_code_context(self, lines: List[Line], target_line_index: int) -> bool:
        """
        Determine if a line is in a code context (distinguishes from monospace headers).
        
        Args:
            lines: All lines for context analysis
            target_line_index: Index of the line to check
            
        Returns:
            True if the line appears to be in a code context
        """
        if not lines or target_line_index < 0 or target_line_index >= len(lines):
            return False

        target_line = lines[target_line_index]
        target_font_family = getattr(target_line, '_font_family', '')

        # If current line is not monospace, it's not code context
        if not self.is_monospace_font(target_font_family):
            return False

        # Check font size - headers typically have larger font sizes
        if target_line.font_size and target_line.font_size > self.config.max_header_font_size:
            return False

        # Check immediate neighbors and surrounding context
        context_radius = 1  # Check 1 line before and after for tight context
        start_idx = max(0, target_line_index - context_radius)
        end_idx = min(len(lines), target_line_index + context_radius + 1)

        context_lines = lines[start_idx:end_idx]
        monospace_count = 0

        for line in context_lines:
            font_family = getattr(line, '_font_family', '')
            if self.is_monospace_font(font_family):
                monospace_count += 1

        # For single line with monospace font, it's considered code
        if len(context_lines) == 1:
            return True

        # If at least half of context is monospace, likely code context
        threshold = 0.5
        return (monospace_count / len(context_lines)) >= threshold

    def _extract_code_style(self, line: Line, font_family: str) -> CodeStyle:
        """
        Extract code style information from a line.
        
        Args:
            line: Line to extract style from
            font_family: Font family of the line
            
        Returns:
            CodeStyle object with extracted information
        """
        # Calculate indentation level based on x_position
        base_x = 10.0  # Assumed base x position
        indentation_unit = 4.0  # Pixels per indentation level

        # Calculate indentation level, treating any indentation as level 1 minimum
        x_offset = line.x_position - base_x
        if x_offset > 1.0:  # Any meaningful indentation
            indentation_level = max(1, int(x_offset / indentation_unit))
        else:
            indentation_level = 0

        # For now, assume spaces (tabs detection would require character analysis)
        uses_tabs = False

        return CodeStyle(
            indentation_level=indentation_level,
            uses_tabs=uses_tabs,
            preserve_whitespace=True,
            font_family=font_family
        )
