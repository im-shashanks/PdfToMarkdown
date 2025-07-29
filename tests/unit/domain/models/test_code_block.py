"""
Unit tests for CodeBlock domain model.

Following TDD methodology - Red phase: Create failing tests first.
"""

import pytest
from pdf2markdown.domain.models.document import CodeBlock, CodeLanguage, CodeStyle, InlineCode, Line


class TestCodeLanguage:
    """Test CodeLanguage enum."""
    
    def test_code_language_enum_values(self):
        """Test that CodeLanguage enum has expected values."""
        assert CodeLanguage.PYTHON.value == "python"
        assert CodeLanguage.JAVASCRIPT.value == "javascript"
        assert CodeLanguage.JAVA.value == "java"
        assert CodeLanguage.CPP.value == "cpp"
        assert CodeLanguage.SQL.value == "sql"
        assert CodeLanguage.HTML.value == "html"
        assert CodeLanguage.JSON.value == "json"
        assert CodeLanguage.UNKNOWN.value == "unknown"
    
    def test_code_language_from_string(self):
        """Test creating CodeLanguage from string representation."""
        assert CodeLanguage.from_string("python") == CodeLanguage.PYTHON
        assert CodeLanguage.from_string("javascript") == CodeLanguage.JAVASCRIPT
        assert CodeLanguage.from_string("unknown_lang") == CodeLanguage.UNKNOWN


class TestCodeStyle:
    """Test CodeStyle value object."""
    
    def test_code_style_creation(self):
        """Test CodeStyle creation with valid parameters."""
        style = CodeStyle(
            indentation_level=2,
            uses_tabs=False,
            preserve_whitespace=True,
            font_family="Courier New"
        )
        assert style.indentation_level == 2
        assert style.uses_tabs is False
        assert style.preserve_whitespace is True
        assert style.font_family == "Courier New"
    
    def test_code_style_defaults(self):
        """Test CodeStyle default values."""
        style = CodeStyle()
        assert style.indentation_level == 0
        assert style.uses_tabs is False
        assert style.preserve_whitespace is True
        assert style.font_family == ""
    
    def test_code_style_immutable(self):
        """Test that CodeStyle is immutable."""
        style = CodeStyle(indentation_level=2)
        with pytest.raises(AttributeError):
            style.indentation_level = 4
    
    def test_code_style_validation(self):
        """Test CodeStyle validation rules."""
        with pytest.raises(ValueError):
            CodeStyle(indentation_level=-1)


class TestInlineCode:
    """Test InlineCode value object."""
    
    def test_inline_code_creation(self):
        """Test InlineCode creation with valid parameters."""
        inline_code = InlineCode(
            content="print('hello')",
            font_family="Monaco",
            start_position=10.0,
            end_position=50.0
        )
        assert inline_code.content == "print('hello')"
        assert inline_code.font_family == "Monaco"
        assert inline_code.start_position == 10.0
        assert inline_code.end_position == 50.0
    
    def test_inline_code_immutable(self):
        """Test that InlineCode is immutable."""
        inline_code = InlineCode(content="test")
        with pytest.raises(AttributeError):
            inline_code.content = "modified"
    
    def test_inline_code_validation(self):
        """Test InlineCode validation rules."""
        with pytest.raises(ValueError):
            InlineCode(content="")  # Empty content
        
        with pytest.raises(ValueError):
            InlineCode(content="test", start_position=50.0, end_position=10.0)  # Invalid positions
    
    def test_inline_code_to_markdown(self):
        """Test InlineCode markdown conversion."""
        inline_code = InlineCode(content="variable_name", font_family="Consolas")
        assert inline_code.to_markdown() == "`variable_name`"
    
    def test_inline_code_special_characters_escaped(self):
        """Test that special markdown characters are escaped in inline code."""
        inline_code = InlineCode(content="func(`param`)")
        assert inline_code.to_markdown() == "`func(\\`param\\`)`"


class TestCodeBlock:
    """Test CodeBlock domain model."""
    
    def test_code_block_creation(self):
        """Test CodeBlock creation with valid parameters."""
        lines = [
            Line("def hello():", 100.0, 10.0, 12.0, font_size=10.0),
            Line("    print('Hello, World!')", 88.0, 10.0, 12.0, font_size=10.0)
        ]
        
        style = CodeStyle(indentation_level=1, font_family="Courier")
        
        code_block = CodeBlock(
            lines=lines,
            language=CodeLanguage.PYTHON,
            style=style
        )
        
        assert len(code_block.lines) == 2
        assert code_block.language == CodeLanguage.PYTHON
        assert code_block.style == style
    
    def test_code_block_content_property(self):
        """Test CodeBlock content property concatenates lines correctly."""
        lines = [
            Line("function test() {", 100.0, 10.0, 12.0),
            Line("  return 42;", 88.0, 10.0, 12.0),
            Line("}", 76.0, 10.0, 12.0)
        ]
        
        code_block = CodeBlock(lines=lines, language=CodeLanguage.JAVASCRIPT)
        expected_content = "function test() {\n  return 42;\n}"
        assert code_block.content == expected_content
    
    def test_code_block_add_line(self):
        """Test adding line to CodeBlock."""
        code_block = CodeBlock(language=CodeLanguage.PYTHON)
        line = Line("print('test')", 100.0, 10.0, 12.0)
        
        code_block.add_line(line)
        assert len(code_block.lines) == 1
        assert code_block.lines[0] == line
    
    def test_code_block_add_line_validation(self):
        """Test validation when adding invalid line to CodeBlock."""
        code_block = CodeBlock(language=CodeLanguage.PYTHON)
        
        with pytest.raises(TypeError):
            code_block.add_line("not a line")
    
    def test_code_block_is_empty(self):
        """Test CodeBlock empty detection."""
        empty_block = CodeBlock(language=CodeLanguage.PYTHON)
        assert empty_block.is_empty() is True
        
        block_with_empty_lines = CodeBlock(
            lines=[Line("   ", 100.0, 10.0, 12.0)],
            language=CodeLanguage.PYTHON
        )
        assert block_with_empty_lines.is_empty() is True
        
        block_with_content = CodeBlock(
            lines=[Line("print('test')", 100.0, 10.0, 12.0)],
            language=CodeLanguage.PYTHON
        )
        assert block_with_content.is_empty() is False
    
    def test_code_block_to_markdown_with_language(self):
        """Test CodeBlock markdown conversion with language specification."""
        lines = [
            Line("def fibonacci(n):", 100.0, 10.0, 12.0),
            Line("    if n <= 1:", 88.0, 14.0, 12.0),
            Line("        return n", 76.0, 18.0, 12.0),
            Line("    return fibonacci(n-1) + fibonacci(n-2)", 64.0, 14.0, 12.0)
        ]
        
        code_block = CodeBlock(lines=lines, language=CodeLanguage.PYTHON)
        
        expected_markdown = """```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```"""
        
        assert code_block.to_markdown() == expected_markdown
    
    def test_code_block_to_markdown_unknown_language(self):
        """Test CodeBlock markdown conversion with unknown language."""
        lines = [Line("some code", 100.0, 10.0, 12.0)]
        code_block = CodeBlock(lines=lines, language=CodeLanguage.UNKNOWN)
        
        expected_markdown = """```
some code
```"""
        
        assert code_block.to_markdown() == expected_markdown
    
    def test_code_block_preserves_whitespace(self):
        """Test that CodeBlock preserves original whitespace and indentation."""
        lines = [
            Line("def test():", 100.0, 10.0, 12.0),
            Line("    # Comment with spaces", 88.0, 14.0, 12.0),
            Line("        nested_call()", 76.0, 18.0, 12.0),
            Line("", 64.0, 10.0, 12.0),  # Empty line
            Line("    return", 52.0, 14.0, 12.0)
        ]
        
        code_block = CodeBlock(lines=lines, language=CodeLanguage.PYTHON)
        markdown = code_block.to_markdown()
        
        assert "    # Comment with spaces" in markdown
        assert "        nested_call()" in markdown
        assert "\n\n    return" in markdown  # Empty line preserved
    
    def test_code_block_inherits_from_block(self):
        """Test that CodeBlock properly inherits from Block."""
        from pdf2markdown.domain.models.document import Block
        
        code_block = CodeBlock(language=CodeLanguage.PYTHON)
        assert isinstance(code_block, Block)
        
        # Should have abstract method implemented
        assert hasattr(code_block, 'to_markdown')
        assert callable(getattr(code_block, 'to_markdown'))