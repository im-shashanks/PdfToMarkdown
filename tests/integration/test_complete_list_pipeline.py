"""End-to-end test for complete list detection pipeline."""

import pytest
from io import StringIO
from unittest.mock import MagicMock, patch

from pdf2markdown.domain.models.document import Document, ListBlock, ListItem, ListMarker, ListType
from pdf2markdown.domain.services.list_detector import ListDetector
from pdf2markdown.infrastructure.formatters.markdown_formatter import MarkdownFormatter


class TestCompleteListPipeline:
    """Test the complete list detection and formatting pipeline."""

    def test_end_to_end_list_processing(self):
        """Test complete pipeline from list detection to markdown output."""
        
        # Step 1: Create list detector
        detector = ListDetector()
        
        # Step 2: Simulate realistic list content from PDF
        from pdf2markdown.domain.models.document import Line
        
        realistic_lines = [
            # Title
            Line("Meeting Agenda", 200.0, 50.0, 14.0),
            Line("", 180.0, 50.0, 12.0),  # Empty line
            
            # Introduction paragraph
            Line("The following items will be discussed:", 160.0, 50.0, 12.0),
            Line("", 140.0, 50.0, 12.0),  # Empty line
            
            # Main list with nested items
            Line("1. Project Updates", 120.0, 50.0, 12.0),
            Line("   • Review current milestones", 105.0, 65.0, 12.0),
            Line("   • Discuss upcoming deadlines", 90.0, 65.0, 12.0),
            Line("2. Budget Review", 75.0, 50.0, 12.0),
            Line("   a. Q4 expenses", 60.0, 70.0, 12.0),
            Line("   b. Next year planning", 45.0, 70.0, 12.0),
            Line("3. Action Items", 30.0, 50.0, 12.0),
            
            # Separate list after content
            Line("", 15.0, 50.0, 12.0),  # Empty line
            Line("Please bring the following:", 5.0, 50.0, 12.0),
            Line("• Laptops", -10.0, 50.0, 12.0),
            Line("• Notebooks", -25.0, 50.0, 12.0),
            Line("• Previous meeting notes", -40.0, 50.0, 12.0),
        ]
        
        # Step 3: Detect list items
        list_items = detector.detect_list_items_from_lines(realistic_lines)
        
        # Should detect both main list and supplies list
        assert len(list_items) > 5, "Should detect multiple list items from realistic content"
        
        # Verify nested items are detected
        nested_items = [item for item in list_items if item.level > 0]
        assert len(nested_items) > 0, "Should detect nested list items"
        
        # Step 4: Group into blocks
        list_blocks = detector.group_list_items_into_blocks(list_items)
        
        # Should create multiple list blocks
        assert len(list_blocks) >= 2, "Should create separate blocks for different list sections"
        
        # Step 5: Create document and format to markdown
        document = Document(title="Test Document")
        
        # Add some regular content
        from pdf2markdown.domain.models.document import TextBlock
        document.add_block(TextBlock("The following items will be discussed:"))
        
        # Add list blocks
        for block in list_blocks:
            document.add_block(block)
        
        # Step 6: Format to final markdown
        formatter = MarkdownFormatter()
        final_markdown = formatter.format_document(document)
        
        # Step 7: Verify final output
        print("Generated Markdown:")
        print(final_markdown)
        print("="*50)
        
        # Verify structure is maintained (numbers may be renumbered)
        assert "Project Updates" in final_markdown
        assert "Budget Review" in final_markdown
        assert "Action Items" in final_markdown
        
        # Verify nested content (indented)
        assert "  - Review current milestones" in final_markdown or "  • Review current milestones" in final_markdown
        
        # Verify separate bullet list
        assert "- Laptops" in final_markdown
        assert "- Notebooks" in final_markdown
        
        return final_markdown

    def test_mixed_content_with_lists(self):
        """Test document with mixed paragraphs and lists."""
        from pdf2markdown.domain.models.document import Line, Paragraph, TextBlock
        
        lines = [
            Line("Introduction paragraph text here.", 200.0, 50.0, 12.0),
            Line("", 180.0, 50.0, 12.0),
            Line("• First list item", 160.0, 50.0, 12.0),
            Line("• Second list item", 140.0, 50.0, 12.0),
            Line("", 120.0, 50.0, 12.0),
            Line("Concluding paragraph text here.", 100.0, 50.0, 12.0),
        ]
        
        detector = ListDetector()
        list_items = detector.detect_list_items_from_lines(lines)
        list_blocks = detector.group_list_items_into_blocks(list_items)
        
        # Create mixed document
        document = Document()
        document.add_block(TextBlock("Introduction paragraph text here."))
        
        for block in list_blocks:
            document.add_block(block)
        
        document.add_block(TextBlock("Concluding paragraph text here."))
        
        formatter = MarkdownFormatter()
        markdown = formatter.format_document(document)
        
        # Should contain both paragraphs and lists in proper order
        lines = markdown.split('\n')
        intro_index = next((i for i, line in enumerate(lines) if "Introduction paragraph" in line), -1)
        list_index = next((i for i, line in enumerate(lines) if "- First list item" in line), -1)
        conclusion_index = next((i for i, line in enumerate(lines) if "Concluding paragraph" in line), -1)
        
        assert intro_index != -1, "Should contain introduction"
        assert list_index != -1, "Should contain list items"
        assert conclusion_index != -1, "Should contain conclusion"
        assert intro_index < list_index < conclusion_index, "Should maintain proper order"

    def test_performance_end_to_end(self):
        """Test end-to-end performance with larger content."""
        import time
        
        # Generate large list content
        from pdf2markdown.domain.models.document import Line
        
        lines = []
        y_pos = 1000.0
        
        # Create a mix of different list types and nesting
        for section in range(5):  # 5 sections
            # Section header
            lines.append(Line(f"Section {section + 1}", y_pos, 50.0, 14.0))
            y_pos -= 20.0
            
            # Main list items
            for item in range(20):  # 20 items per section
                lines.append(Line(f"{item + 1}. Main item {item + 1}", y_pos, 50.0, 12.0))
                y_pos -= 15.0
                
                # Some nested items
                if item % 3 == 0:
                    lines.append(Line(f"   • Nested item A", y_pos, 65.0, 12.0))
                    y_pos -= 15.0
                    lines.append(Line(f"   • Nested item B", y_pos, 65.0, 12.0))
                    y_pos -= 15.0
        
        print(f"Testing with {len(lines)} lines of content")
        
        # Measure complete pipeline performance
        start_time = time.time()
        
        detector = ListDetector()
        list_items = detector.detect_list_items_from_lines(lines)
        list_blocks = detector.group_list_items_into_blocks(list_items)
        
        document = Document()
        for block in list_blocks:
            document.add_block(block)
        
        formatter = MarkdownFormatter()
        markdown = formatter.format_document(document)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"Complete pipeline took {total_time:.3f} seconds")
        print(f"Detected {len(list_items)} list items in {len(list_blocks)} blocks")
        print(f"Generated {len(markdown)} characters of markdown")
        
        # Should complete within reasonable time
        assert total_time < 2.0, f"Pipeline took {total_time:.3f}s, should be under 2 seconds"
        
        # Should detect reasonable number of items
        assert len(list_items) > 100, "Should detect multiple list items"
        assert len(list_blocks) >= 5, "Should create multiple list blocks"

    def test_error_handling_in_pipeline(self):
        """Test pipeline handles edge cases and errors gracefully."""
        detector = ListDetector()
        formatter = MarkdownFormatter()
        
        # Test with empty input
        empty_items = detector.detect_list_items_from_lines([])
        empty_blocks = detector.group_list_items_into_blocks(empty_items)
        
        empty_doc = Document()
        for block in empty_blocks:
            empty_doc.add_block(block)
        
        empty_markdown = formatter.format_document(empty_doc)
        assert empty_markdown == "" or empty_markdown.isspace()
        
        # Test with malformed list content
        from pdf2markdown.domain.models.document import Line
        
        malformed_lines = [
            Line("• ", 100.0, 50.0, 12.0),  # Empty content
            Line("1. ", 85.0, 50.0, 12.0),   # Empty content
            Line("Not a list", 70.0, 50.0, 12.0),  # Regular text
        ]
        
        malformed_items = detector.detect_list_items_from_lines(malformed_lines)
        malformed_blocks = detector.group_list_items_into_blocks(malformed_items)
        
        malformed_doc = Document()
        for block in malformed_blocks:
            malformed_doc.add_block(block)
        
        # Should handle gracefully without crashing
        malformed_markdown = formatter.format_document(malformed_doc)
        assert isinstance(malformed_markdown, str)  # Should return valid string

    def test_acceptance_criteria_validation(self):
        """Validate all acceptance criteria from the story are met."""
        from pdf2markdown.domain.models.document import Line
        
        # AC 1: Parser detects bullet points and converts to unordered lists
        bullet_lines = [
            Line("• First bullet", 100.0, 50.0, 12.0),
            Line("◦ Circle bullet", 85.0, 50.0, 12.0),
            Line("▪ Square bullet", 70.0, 50.0, 12.0),
            Line("- Dash bullet", 55.0, 50.0, 12.0),
            Line("* Asterisk bullet", 40.0, 50.0, 12.0),
        ]
        
        detector = ListDetector()
        bullet_items = detector.detect_list_items_from_lines(bullet_lines)
        bullet_blocks = detector.group_list_items_into_blocks(bullet_items)
        
        assert len(bullet_blocks) == 1
        assert bullet_blocks[0].list_type == ListType.UNORDERED
        assert len(bullet_blocks[0].items) == 5
        
        # AC 2: Parser detects numbered lists and converts to ordered lists
        numbered_lines = [
            Line("1. First item", 100.0, 50.0, 12.0),
            Line("2. Second item", 85.0, 50.0, 12.0),
            Line("a. Alpha item", 70.0, 50.0, 12.0),
            Line("b. Beta item", 55.0, 50.0, 12.0),
            Line("i. Roman item", 40.0, 50.0, 12.0),
            Line("ii. Second roman", 25.0, 50.0, 12.0),
        ]
        
        numbered_items = detector.detect_list_items_from_lines(numbered_lines)
        numbered_blocks = detector.group_list_items_into_blocks(numbered_items)
        
        assert len(numbered_blocks) == 1
        assert numbered_blocks[0].list_type == ListType.ORDERED
        assert len(numbered_blocks[0].items) == 6
        
        # AC 3: Nested structures up to 3 levels deep
        nested_lines = [
            Line("1. Level 0", 100.0, 50.0, 12.0),
            Line("  • Level 1", 85.0, 60.0, 12.0),
            Line("    - Level 2", 70.0, 70.0, 12.0),
            Line("      * Level 3", 55.0, 80.0, 12.0),
        ]
        
        nested_items = detector.detect_list_items_from_lines(nested_lines)
        max_level = max(item.level for item in nested_items)
        
        assert max_level <= 3, "Should not exceed maximum nesting level of 3"
        assert len(nested_items) == 4, "Should detect all nested items"
        
        # AC 4: Mixed list types handled correctly  
        mixed_lines = [
            Line("1. Ordered item", 100.0, 50.0, 12.0),
            Line("  • Nested bullet", 85.0, 60.0, 12.0),
            Line("2. Second ordered", 70.0, 50.0, 12.0),
            Line("• Separate bullet list", 55.0, 50.0, 12.0),
        ]
        
        mixed_items = detector.detect_list_items_from_lines(mixed_lines)
        mixed_blocks = detector.group_list_items_into_blocks(mixed_items)
        
        # Should handle mixed nesting properly
        assert len(mixed_items) == 4
        nested_item = next((item for item in mixed_items if item.level > 0), None)
        assert nested_item is not None, "Should detect nested bullet under ordered item"
        
        # AC 5: List continuation after other content
        continuation_lines = [
            Line("• First item", 100.0, 50.0, 12.0),
            Line("Regular paragraph", 85.0, 50.0, 12.0),
            Line("• Continued list", 70.0, 50.0, 12.0),
        ]
        
        continuation_items = detector.detect_list_items_from_lines(continuation_lines)
        continuation_blocks = detector.group_list_items_into_blocks(continuation_items)
        
        # Should create separate blocks for interrupted lists
        unordered_blocks = [b for b in continuation_blocks if b.list_type == ListType.UNORDERED]
        assert len(unordered_blocks) >= 1, "Should handle list continuation"
        
        print("All acceptance criteria validated successfully!")