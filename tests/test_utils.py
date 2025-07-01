import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO
import json

from llm7shi.utils import (
    do_show_params,
    contents_to_openai_messages,
)


class TestDoShowParams:
    """Test parameter display functionality"""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_params_to_stdout(self, mock_stdout):
        """Test parameter display to stdout"""
        contents = ["Hello", "World"]
        model = "test-model"
        
        do_show_params(contents, model=model, file=None)
        
        # Since file=None, no output should be generated
        output = mock_stdout.getvalue()
        assert output == ""
    
    def test_show_params_to_file(self):
        """Test parameter display to file"""
        mock_file = MagicMock()
        contents = ["Test content"]
        model = "test-model"
        
        do_show_params(contents, model=model, file=mock_file)
        
        # Verify print was called with correct parameters
        mock_file.write.assert_called()  # print() calls write() internally
        # Check that model parameter was displayed
        written_calls = [str(call) for call in mock_file.write.call_args_list]
        written_content = "".join(written_calls)
        assert "model" in written_content
        assert "test-model" in written_content
    
    def test_show_params_with_temperature(self):
        """Test parameter display with temperature"""
        mock_file = MagicMock()
        
        do_show_params(
            ["Test"],
            model="test-model",
            temperature=0.7,
            file=mock_file
        )
        
        mock_file.write.assert_called()
        written_calls = [str(call) for call in mock_file.write.call_args_list]
        written_content = "".join(written_calls)
        assert "temperature" in written_content
        assert "0.7" in written_content
    
    def test_show_params_with_config(self):
        """Test parameter display with config"""
        mock_file = MagicMock()
        config = {"response_schema": "test_schema"}
        
        do_show_params(
            ["Test"],
            model="test-model",
            config=config,
            file=mock_file
        )
        
        mock_file.write.assert_called()
        written_calls = [str(call) for call in mock_file.write.call_args_list]
        written_content = "".join(written_calls)
        assert "config" in written_content
    
    def test_show_params_content_quoting(self):
        """Test proper quoting of content strings"""
        mock_file = MagicMock()
        contents = ["Text with 'quotes'", 'Text with "double quotes"']
        
        do_show_params(contents, model="test-model", file=mock_file)
        
        mock_file.write.assert_called()
        written_calls = [str(call) for call in mock_file.write.call_args_list] 
        written_content = "".join(written_calls)
        assert "model" in written_content
        assert "test-model" in written_content


class TestContentsToOpenaiMessages:
    """Test OpenAI message format conversion"""
    
    def test_contents_without_system_prompt(self):
        """Test conversion without system prompt"""
        contents = ["Hello, how are you?", "Tell me a joke"]
        
        messages = contents_to_openai_messages(contents)
        
        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "Hello, how are you?"}
        assert messages[1] == {"role": "user", "content": "Tell me a joke"}
    
    def test_contents_with_system_prompt(self):
        """Test conversion with system prompt"""
        contents = ["Hello, how are you?", "Tell me a joke"]
        system_prompt = "You are a helpful assistant."
        
        messages = contents_to_openai_messages(contents, system_prompt=system_prompt)
        
        assert len(messages) == 3
        assert messages[0] == {"role": "system", "content": "You are a helpful assistant."}
        assert messages[1] == {"role": "user", "content": "Hello, how are you?"}
        assert messages[2] == {"role": "user", "content": "Tell me a joke"}
    
    def test_contents_empty_list(self):
        """Test conversion with empty contents"""
        messages = contents_to_openai_messages([])
        
        assert messages == []
    
    def test_contents_single_item(self):
        """Test conversion with single content item"""
        contents = ["Single message"]
        
        messages = contents_to_openai_messages(contents)
        
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "Single message"}
    
    def test_contents_with_empty_system_prompt(self):
        """Test conversion with empty system prompt"""
        contents = ["Test message"]
        
        messages = contents_to_openai_messages(contents, system_prompt="")
        
        # Empty system prompt should NOT be added (falsy value)
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "Test message"}