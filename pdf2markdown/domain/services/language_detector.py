"""
Language detection service for identifying programming languages in code blocks.

Follows Clean Architecture principles with dependency inversion.
"""

import re
from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

from pdf2markdown.domain.interfaces.language_detector import LanguageDetectorInterface
from pdf2markdown.domain.models.document import CodeBlock
from pdf2markdown.domain.models.document import CodeLanguage


@dataclass
class LanguagePattern:
    """Pattern matching configuration for a programming language."""
    keywords: Set[str] = field(default_factory=set)
    syntax_patterns: List[str] = field(default_factory=list)  # Regex patterns
    distinctive_chars: Set[str] = field(default_factory=set)
    weight: float = 1.0


class LanguageDetector(LanguageDetectorInterface):
    """
    Service for detecting programming languages in code content.
    
    Follows Single Responsibility Principle - only responsible for language detection.
    """

    def __init__(self, custom_patterns: Optional[Dict[str, List[str]]] = None):
        """
        Initialize LanguageDetector with language detection patterns.
        
        Args:
            custom_patterns: Optional custom patterns for specific languages
        """
        self.patterns = self._initialize_language_patterns()

        # Add custom patterns if provided
        if custom_patterns:
            self._add_custom_patterns(custom_patterns)

        # Pre-compile regex patterns for performance
        self._compile_patterns()

    def detect_language(self, code_content: str) -> CodeLanguage:
        """
        Detect the programming language of code content.
        
        Args:
            code_content: The code content to analyze
            
        Returns:
            Detected programming language or UNKNOWN if cannot be determined
        """
        if not code_content.strip():
            return CodeLanguage.UNKNOWN

        scores = {}

        # Combine keyword and syntax detection
        keyword_result = self.detect_language_from_keywords(code_content)
        syntax_result = self.detect_language_from_syntax(code_content)

        # Calculate confidence scores for all languages
        for language in CodeLanguage:
            if language == CodeLanguage.UNKNOWN:
                continue

            confidence = self.get_confidence_score(code_content, language)
            scores[language] = confidence

        # Return the language with highest confidence
        if scores:
            best_language = max(scores.keys(), key=lambda lang: scores[lang])
            if scores[best_language] > 0.1:  # Lower confidence threshold
                return best_language

        return CodeLanguage.UNKNOWN

    def detect_language_from_keywords(self, code_content: str) -> CodeLanguage:
        """
        Detect language based on keyword patterns.
        
        Args:
            code_content: The code content to analyze
            
        Returns:
            Detected programming language based on keywords
        """
        content_lower = code_content.lower()
        word_counts = Counter()

        # Count keyword matches for each language
        for language, pattern in self.patterns.items():
            if language == CodeLanguage.UNKNOWN:
                continue

            count = 0
            for keyword in pattern.keywords:
                # Use word boundaries to avoid partial matches
                if re.search(rf'\b{re.escape(keyword.lower())}\b', content_lower):
                    count += 1

            word_counts[language] = count * pattern.weight

        if word_counts:
            return word_counts.most_common(1)[0][0]

        return CodeLanguage.UNKNOWN

    def detect_language_from_syntax(self, code_content: str) -> CodeLanguage:
        """
        Detect language based on syntax patterns.
        
        Args:
            code_content: The code content to analyze
            
        Returns:
            Detected programming language based on syntax patterns
        """
        syntax_scores = Counter()

        for language, pattern in self.patterns.items():
            if language == CodeLanguage.UNKNOWN:
                continue

            score = 0

            # Check compiled regex patterns
            for compiled_pattern in pattern.syntax_patterns:
                matches = compiled_pattern.findall(code_content)
                score += len(matches)

            # Check distinctive characters
            for char in pattern.distinctive_chars:
                score += code_content.count(char) * 0.1

            syntax_scores[language] = score * pattern.weight

        if syntax_scores:
            return syntax_scores.most_common(1)[0][0]

        return CodeLanguage.UNKNOWN

    def analyze_code_block(self, code_block: CodeBlock) -> CodeBlock:
        """
        Analyze a code block and update it with detected language.
        
        Args:
            code_block: The code block to analyze
            
        Returns:
            Code block with updated language information
        """
        content = code_block.content
        detected_language = self.detect_language(content)

        # Create new code block with updated language
        return CodeBlock(
            lines=code_block.lines,
            language=detected_language,
            style=code_block.style
        )

    def get_confidence_score(self, code_content: str, language: CodeLanguage) -> float:
        """
        Get confidence score for a specific language detection.
        
        Args:
            code_content: The code content to analyze
            language: The language to score confidence for
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if language == CodeLanguage.UNKNOWN or not code_content.strip():
            return 0.0

        if language not in self.patterns:
            return 0.0

        pattern = self.patterns[language]
        content_lower = code_content.lower()

        # Calculate keyword confidence
        keyword_matches = 0
        total_keywords = len(pattern.keywords)

        if total_keywords > 0:
            for keyword in pattern.keywords:
                if re.search(rf'\b{re.escape(keyword.lower())}\b', content_lower):
                    keyword_matches += 1

            keyword_confidence = keyword_matches / total_keywords
        else:
            keyword_confidence = 0.0

        # Calculate syntax confidence
        syntax_matches = 0
        total_patterns = len(pattern.syntax_patterns)

        if total_patterns > 0:
            for compiled_pattern in pattern.syntax_patterns:
                if compiled_pattern.search(code_content):
                    syntax_matches += 1

            syntax_confidence = syntax_matches / total_patterns
        else:
            syntax_confidence = 0.0

        # Calculate character confidence
        char_score = 0
        if pattern.distinctive_chars:
            for char in pattern.distinctive_chars:
                char_score += code_content.count(char)

            # Normalize by content length
            char_confidence = min(char_score / len(code_content), 1.0)
        else:
            char_confidence = 0.0

        # Weighted combination of confidence scores
        # Use max instead of weighted average to be more generous
        individual_scores = [keyword_confidence, syntax_confidence, char_confidence]
        best_individual_score = max(individual_scores) if individual_scores else 0.0

        # Also compute weighted average
        weighted_average = (
            keyword_confidence * 0.5 +
            syntax_confidence * 0.3 +
            char_confidence * 0.2
        )

        # Take the better of the two approaches
        overall_confidence = max(best_individual_score * 0.7, weighted_average) * pattern.weight

        return min(overall_confidence, 1.0)

    def _initialize_language_patterns(self) -> Dict[CodeLanguage, LanguagePattern]:
        """Initialize built-in language detection patterns."""
        patterns = {}

        # Python patterns
        patterns[CodeLanguage.PYTHON] = LanguagePattern(
            keywords={
                'def', 'class', 'import', 'from', 'if', 'elif', 'else',
                'for', 'while', 'try', 'except', 'finally', 'with',
                'lambda', 'yield', 'return', 'pass', 'break', 'continue',
                'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None',
                '__init__', '__main__', 'self', 'print'
            },
            syntax_patterns=[
                r'def\s+\w+\s*\(',  # Function definitions
                r'class\s+\w+\s*[:\(]',  # Class definitions
                r'import\s+\w+',  # Import statements
                r'from\s+\w+\s+import',  # From imports
                r'if\s+__name__\s*==\s*["\']__main__["\']',  # Main guard
                r':\s*\n\s+',  # Indentation after colon
            ],
            distinctive_chars={':', '#'},
            weight=1.0
        )

        # JavaScript patterns
        patterns[CodeLanguage.JAVASCRIPT] = LanguagePattern(
            keywords={
                'function', 'var', 'let', 'const', 'if', 'else', 'for',
                'while', 'do', 'switch', 'case', 'default', 'break',
                'continue', 'return', 'try', 'catch', 'finally', 'throw',
                'new', 'this', 'prototype', 'typeof', 'instanceof',
                'console.log', 'document', 'window', 'null', 'undefined',
                'true', 'false'
            },
            syntax_patterns=[
                r'function\s+\w*\s*\(',  # Function declarations
                r'\w+\s*=>\s*[\{\w]',  # Arrow functions
                r'(var|let|const)\s+\w+',  # Variable declarations
                r'console\.log\s*\(',  # Console logging
                r'document\.\w+',  # DOM access
                r'\{\s*[\w\s,:"\']+\s*\}',  # Object literals
            ],
            distinctive_chars={'{', '}', ';'},
            weight=1.0
        )

        # Java patterns
        patterns[CodeLanguage.JAVA] = LanguagePattern(
            keywords={
                'public', 'private', 'protected', 'static', 'final',
                'class', 'interface', 'extends', 'implements', 'abstract',
                'void', 'int', 'String', 'boolean', 'double', 'float',
                'char', 'byte', 'short', 'long', 'if', 'else', 'for',
                'while', 'do', 'switch', 'case', 'default', 'break',
                'continue', 'return', 'try', 'catch', 'finally', 'throw',
                'throws', 'new', 'this', 'super', 'null', 'true', 'false',
                'System.out.println'
            },
            syntax_patterns=[
                r'public\s+(static\s+)?void\s+main',  # Main method
                r'public\s+class\s+\w+',  # Public class
                r'System\.out\.print',  # System output
                r'String\[\]\s+\w+',  # String array
                r'@\w+',  # Annotations
            ],
            distinctive_chars={'{', '}', ';'},
            weight=1.0
        )

        # C++ patterns
        patterns[CodeLanguage.CPP] = LanguagePattern(
            keywords={
                'include', 'namespace', 'using', 'class', 'struct',
                'public', 'private', 'protected', 'virtual', 'static',
                'const', 'int', 'char', 'float', 'double', 'bool',
                'void', 'auto', 'if', 'else', 'for', 'while',
                'do', 'switch', 'case', 'default', 'break', 'continue',
                'return', 'try', 'catch', 'throw', 'new', 'delete',
                'this', 'nullptr', 'true', 'false', 'cout', 'cin',
                'endl', 'std', 'vector', 'string', 'printf'
            },
            syntax_patterns=[
                r'#include\s*<[\w\.]+>',  # Include statements
                r'std::\w+',  # Standard library usage
                r'\w+\s*\*+\s*\w+',  # Pointer declarations
                r'cout\s*<<',  # Output stream
                r'cin\s*>>',  # Input stream
                r'::\w+',  # Scope resolution
            ],
            distinctive_chars={'*', '&', '<', '>', '#'},
            weight=1.0
        )

        # SQL patterns
        patterns[CodeLanguage.SQL] = LanguagePattern(
            keywords={
                'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
                'CREATE', 'DROP', 'ALTER', 'TABLE', 'INDEX', 'VIEW',
                'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON',
                'GROUP', 'BY', 'ORDER', 'HAVING', 'UNION', 'ALL',
                'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
                'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'LIKE',
                'BETWEEN', 'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
            },
            syntax_patterns=[
                r'SELECT\s+[\w\s,\*]+\s+FROM',  # SELECT queries
                r'INSERT\s+INTO\s+\w+',  # INSERT statements
                r'UPDATE\s+\w+\s+SET',  # UPDATE statements
                r'DELETE\s+FROM\s+\w+',  # DELETE statements
                r'CREATE\s+TABLE\s+\w+',  # CREATE TABLE
                r'\w+\s*=\s*[\'"][^\'"]*[\'"]',  # String comparisons
            ],
            distinctive_chars={';'},
            weight=1.0
        )

        # HTML patterns
        patterns[CodeLanguage.HTML] = LanguagePattern(
            keywords={
                'html', 'head', 'body', 'title', 'meta', 'link',
                'script', 'style', 'div', 'span', 'p', 'h1', 'h2',
                'h3', 'h4', 'h5', 'h6', 'a', 'img', 'ul', 'ol',
                'li', 'table', 'tr', 'td', 'th', 'form', 'input',
                'button', 'select', 'option', 'textarea', 'DOCTYPE'
            },
            syntax_patterns=[
                r'<\s*\w+[^>]*>',  # Opening tags
                r'<\s*/\s*\w+\s*>',  # Closing tags
                r'<!DOCTYPE\s+html>',  # DOCTYPE declaration
                r'\w+\s*=\s*["\'][^"\']*["\']',  # Attributes
                r'<!--.*?-->',  # Comments
            ],
            distinctive_chars={'<', '>', '/', '=', '"', "'"},
            weight=1.0
        )

        # JSON patterns
        patterns[CodeLanguage.JSON] = LanguagePattern(
            keywords={
                'true', 'false', 'null'
            },
            syntax_patterns=[
                r'\{\s*"[\w\s]+"\s*:\s*["\w\[\{]',  # Object with string keys
                r'"\w+"\s*:\s*\{',  # Nested objects
                r'"\w+"\s*:\s*\[',  # Arrays
                r'"\w+"\s*:\s*(true|false|null|\d+)',  # Primitive values
                r'\[\s*\{',  # Array of objects
            ],
            distinctive_chars={'{', '}', '[', ']', ':', ',', '"'},
            weight=1.0
        )

        return patterns

    def _add_custom_patterns(self, custom_patterns: Dict[str, List[str]]) -> None:
        """Add custom patterns to existing language patterns."""
        for lang_name, keywords in custom_patterns.items():
            try:
                language = CodeLanguage(lang_name.lower())
                if language in self.patterns:
                    self.patterns[language].keywords.update(keywords)
            except ValueError:
                # Ignore unknown languages
                continue

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        for language, pattern in self.patterns.items():
            compiled_patterns = []
            for regex_pattern in pattern.syntax_patterns:
                try:
                    compiled_patterns.append(re.compile(regex_pattern, re.IGNORECASE | re.MULTILINE))
                except re.error:
                    # Skip invalid patterns
                    continue
            pattern.syntax_patterns = compiled_patterns
