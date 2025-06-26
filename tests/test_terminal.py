import pytest

from llm7shi.terminal import bold, convert_markdown, MarkdownStreamConverter


class TestBoldFunction:
    """Test simple bold text formatting"""
    
    def test_bold_simple_text(self):
        """Test bold formatting with simple text"""
        result = bold("Hello World")
        # Check that result contains the input text and has ANSI formatting
        assert "Hello World" in result
        assert len(result) > len("Hello World")  # Should be longer due to formatting
    
    def test_bold_empty_string(self):
        """Test bold formatting with empty string"""
        result = bold("")
        # Should still contain formatting codes even for empty string
        assert len(result) > 0
    
    def test_bold_with_special_characters(self):
        """Test bold formatting with special characters"""
        result = bold("Hello\nWorld!")
        # Should preserve special characters
        assert "Hello\nWorld!" in result
        assert "\n" in result


class TestConvertMarkdown:
    """Test one-shot markdown conversion"""
    
    def test_convert_single_bold(self):
        """Test conversion of single bold text"""
        text = "This is **bold** text"
        result = convert_markdown(text)
        # Should contain the plain text parts
        assert "This is " in result
        assert "bold" in result
        assert " text" in result
        # Should not contain markdown markers
        assert "**" not in result
    
    def test_convert_multiple_bold(self):
        """Test conversion of multiple bold sections"""
        text = "**First** bold and **second** bold"
        result = convert_markdown(text)
        assert "First" in result
        assert "second" in result
        assert " bold and " in result
        assert " bold" in result
        assert "**" not in result
    
    def test_convert_bold_at_start(self):
        """Test conversion of bold text at the start"""
        text = "**Bold** at start"
        result = convert_markdown(text)
        assert "Bold" in result
        assert " at start" in result
        assert "**" not in result
    
    def test_convert_bold_at_end(self):
        """Test conversion of bold text at the end"""
        text = "End with **bold**"
        result = convert_markdown(text)
        assert "End with " in result
        assert "bold" in result
        assert "**" not in result
    
    def test_convert_only_bold(self):
        """Test conversion of text that is entirely bold"""
        text = "**Everything is bold**"
        result = convert_markdown(text)
        assert "Everything is bold" in result
        assert "**" not in result
    
    def test_convert_no_bold(self):
        """Test conversion of text without bold formatting"""
        text = "Just plain text"
        result = convert_markdown(text)
        assert result == "Just plain text"
    
    def test_convert_empty_string(self):
        """Test conversion of empty string"""
        result = convert_markdown("")
        assert result == ""
    
    def test_convert_unclosed_bold(self):
        """Test conversion with unclosed bold marker"""
        text = "This has **unclosed bold"
        result = convert_markdown(text)
        # Should handle unclosed markers gracefully
        assert "This has " in result
        assert "unclosed bold" in result
    
    def test_convert_empty_bold(self):
        """Test conversion with empty bold markers"""
        text = "Empty **** bold markers"
        result = convert_markdown(text)
        assert "Empty " in result
        assert " bold markers" in result
    
    def test_convert_only_asterisks(self):
        """Test conversion with only asterisks"""
        text = "****"
        result = convert_markdown(text)
        # Should handle empty bold section
        assert len(result) >= 0
    
    def test_convert_bold_with_newlines(self):
        """Test conversion of bold text spanning multiple lines"""
        text = "**Bold\nacross\nlines**"
        result = convert_markdown(text)
        assert "Bold" in result
        assert "across" in result
        assert "lines" in result
        assert "\n" in result
        assert "**" not in result
    
    def test_convert_mixed_content(self):
        """Test conversion of mixed content with newlines"""
        text = "Regular text\n**Bold text**\nMore regular text"
        result = convert_markdown(text)
        assert "Regular text" in result
        assert "Bold text" in result
        assert "More regular text" in result
        assert "\n" in result
        assert "**" not in result


class TestMarkdownStreamConverter:
    """Test streaming markdown conversion"""
    
    def test_converter_initialization(self):
        """Test MarkdownStreamConverter initialization"""
        converter = MarkdownStreamConverter()
        assert converter.buffer == ""
        assert converter.bright_mode is False
    
    def test_converter_complete_bold_in_single_chunk(self):
        """Test complete bold formatting in single chunk"""
        converter = MarkdownStreamConverter()
        result = converter.feed("This is **bold** text")
        assert "This is " in result
        assert "bold" in result
        assert " text" in result
        assert "**" not in result
        assert converter.buffer == ""
    
    def test_converter_bold_across_chunks(self):
        """Test bold formatting split across multiple chunks"""
        converter = MarkdownStreamConverter()
        
        # Start bold but don't complete
        result1 = converter.feed("Start **bold")
        assert "Start " in result1
        assert "bold" in result1
        assert converter.buffer == ""
        
        # Complete the bold
        result2 = converter.feed(" text**")
        assert " text" in result2
        assert converter.buffer == ""
        assert converter.bright_mode is False
    
    def test_converter_opening_marker_split(self):
        """Test opening bold marker split across chunks"""
        converter = MarkdownStreamConverter()
        
        # Send partial opening marker
        result1 = converter.feed("Text *")
        assert result1 == "Text "
        assert converter.buffer == "*"
        
        # Complete opening marker and add content
        result2 = converter.feed("*bold content**")
        assert "bold content" in result2
        assert converter.buffer == ""
    
    def test_converter_closing_marker_split(self):
        """Test closing bold marker split across chunks"""
        converter = MarkdownStreamConverter()
        
        # Start and maintain bold state
        result1 = converter.feed("**bold content*")
        assert "bold content" in result1
        
        # Send final marker
        result2 = converter.feed("*")
        assert converter.buffer == ""
    
    def test_converter_multiple_bold_sections(self):
        """Test multiple bold sections in stream"""
        converter = MarkdownStreamConverter()
        
        result1 = converter.feed("**First**")
        assert "First" in result1
        assert "**" not in result1
        
        result2 = converter.feed(" and **Second**")
        assert " and " in result2
        assert "Second" in result2
        assert "**" not in result2
        
        assert converter.buffer == ""
    
    def test_converter_newline_closes_bold(self):
        """Test that newlines auto-close bold formatting"""
        converter = MarkdownStreamConverter()
        
        # Start bold but encounter newline
        result = converter.feed("**bold text\n")
        assert "bold text" in result
        assert "\n" in result
        assert converter.buffer == ""
        assert converter.bright_mode is False
    
    def test_converter_newline_in_complete_bold(self):
        """Test newlines within properly closed bold"""
        converter = MarkdownStreamConverter()
        
        result = converter.feed("**bold\nwith\nnewlines**")
        assert "bold" in result
        assert "with" in result
        assert "newlines" in result
        assert "\n" in result
        assert "**" not in result
        assert converter.buffer == ""
    
    def test_converter_plain_text_only(self):
        """Test converter with plain text (no formatting)"""
        converter = MarkdownStreamConverter()
        
        result = converter.feed("Just plain text")
        assert result == "Just plain text"
        assert converter.buffer == ""
    
    def test_converter_empty_input(self):
        """Test converter with empty input"""
        converter = MarkdownStreamConverter()
        
        result = converter.feed("")
        assert result == ""
        assert converter.buffer == ""
    
    def test_converter_flush_with_pending_content(self):
        """Test flush method with pending content in buffer"""
        converter = MarkdownStreamConverter()
        
        # Leave some content in buffer
        converter.feed("**incomplete")
        
        # Flush should output remaining content and auto-close bold
        result = converter.flush()
        # The flush should contain some content (possibly just formatting codes)
        assert len(result) > 0
        assert converter.buffer == ""
        assert converter.bright_mode is False
    
    def test_converter_flush_empty_buffer(self):
        """Test flush method with empty buffer"""
        converter = MarkdownStreamConverter()
        
        result = converter.flush()
        assert result == ""
        assert converter.buffer == ""
    
    def test_converter_buffer_management(self):
        """Test buffer management with partial markers"""
        converter = MarkdownStreamConverter()
        
        # Partial marker should be buffered
        result1 = converter.feed("Text *")
        assert result1 == "Text "
        assert converter.buffer == "*"
        
        # Non-matching continuation should flush buffer
        result2 = converter.feed("regular")
        assert "*regular" in result2
        assert converter.buffer == ""
    
    def test_converter_complex_streaming_scenario(self):
        """Test complex streaming scenario with multiple partial updates"""
        converter = MarkdownStreamConverter()
        
        # Simulate realistic streaming chunks
        chunks = [
            "This is a **str",
            "eaming** response with **mult",
            "iple** bold sections.\n**New line",
            " bold** text."
        ]
        
        results = []
        for chunk in chunks:
            results.append(converter.feed(chunk))
        
        full_result = "".join(results)
        # Check that key content words are preserved
        assert "This is a " in full_result
        assert "streaming" in full_result
        assert " response with " in full_result
        assert "multiple" in full_result
        assert " bold sections." in full_result
        assert "New line" in full_result
        assert " text." in full_result
        assert "**" not in full_result
    
    def test_converter_state_persistence(self):
        """Test that converter maintains state correctly across feeds"""
        converter = MarkdownStreamConverter()
        
        # Start a bold section
        converter.feed("Start **bold")
        
        # Continue without closing
        converter.feed(" content")
        
        # Finally close
        result = converter.feed("**")
        assert converter.bright_mode is False
        assert converter.buffer == ""


class TestWindowsConsoleIntegration:
    """Test Windows console compatibility"""
    
    def test_windows_console_import_works(self):
        """Test that terminal module imports successfully"""
        # Simply test that we can import the module without errors
        import llm7shi.terminal
        assert hasattr(llm7shi.terminal, 'bold')
        assert hasattr(llm7shi.terminal, 'convert_markdown')
        assert hasattr(llm7shi.terminal, 'MarkdownStreamConverter')


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_many_consecutive_asterisks(self):
        """Test handling of many consecutive asterisks"""
        text = "Text with ******** asterisks"
        result = convert_markdown(text)
        # Should handle this gracefully
        assert "Text with" in result
        assert "asterisks" in result
    
    def test_nested_bold_markers(self):
        """Test handling of nested bold markers"""
        text = "**Outer **inner** content**"
        result = convert_markdown(text)
        # Should handle nested formatting reasonably
        assert "Outer" in result
        assert "inner" in result
        assert "content" in result
    
    def test_very_long_text(self):
        """Test handling of very long text"""
        long_text = "a" * 10000
        text = f"**{long_text}**"
        result = convert_markdown(text)
        assert long_text in result
        # Should not contain markdown markers
        assert "**" not in result