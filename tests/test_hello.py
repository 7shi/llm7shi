import os
import pytest
from unittest.mock import patch, MagicMock
from llm7shi import generate_content_retry


class MockChunk:
    def __init__(self, text, is_thought=False):
        self.candidates = [MagicMock()]
        self.candidates[0].content = MagicMock()
        self.candidates[0].content.parts = [MagicMock()]
        self.candidates[0].content.parts[0].text = text
        self.candidates[0].content.parts[0].thought = is_thought


@pytest.fixture(autouse=True)
def set_dummy_api_key(monkeypatch):
    """Set dummy API key for all tests"""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")


@patch('llm7shi.gemini.client.models.generate_content_stream')
def test_hello_example(mock_stream):
    """Test hello.py example functionality"""
    # Mock response chunks
    mock_chunks = [
        MockChunk("Hello there! "),
        MockChunk("A classic greeting.\n\n"),
        MockChunk("How can I help you today?")
    ]
    mock_stream.return_value = iter(mock_chunks)
    
    # Test the generate_content_retry call from hello.py
    response = generate_content_retry(["Hello, World!"], file=None)
    
    # Verify the call was made
    mock_stream.assert_called_once()
    
    # Check response structure
    assert hasattr(response, 'text')
    assert hasattr(response, 'thoughts')
    assert hasattr(response, 'model')
    assert hasattr(response, 'chunks')
    
    # Verify response content
    expected_text = "Hello there! A classic greeting.\n\nHow can I help you today?"
    assert response.text == expected_text
    assert response.model == "gemini-2.5-flash"
    assert len(response.chunks) == 3
    
    # Verify call arguments
    call_args = mock_stream.call_args
    assert call_args[1]['contents'] == ["Hello, World!"]
    assert call_args[1]['model'] == "gemini-2.5-flash"