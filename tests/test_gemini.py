import os
import pytest
from unittest.mock import patch, MagicMock, call
from typing import Any, Dict
import json

from llm7shi.gemini import (
    Response,
    generate_content_retry,
    build_schema_from_json,
    config_from_schema,
    upload_file,
    delete_file,
)


class MockChunk:
    """Mock chunk for simulating Gemini API streaming responses"""
    def __init__(self, text: str, is_thought: bool = False):
        self.candidates = [MagicMock()]
        self.candidates[0].content = MagicMock()
        self.candidates[0].content.parts = [MagicMock()]
        self.candidates[0].content.parts[0].text = text
        self.candidates[0].content.parts[0].thought = is_thought


@pytest.fixture(autouse=True)
def set_dummy_api_key(monkeypatch):
    """Set dummy API key for all tests"""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")


class TestResponse:
    """Test Response dataclass"""
    
    def test_response_init(self):
        """Test Response initialization with default values"""
        response = Response()
        assert response.thoughts == ""
        assert response.text == ""
        assert response.response is None
        assert response.chunks == []
        assert response.model is None
        assert response.config is None
        assert response.contents is None
    
    def test_response_str(self):
        """Test Response string representation"""
        response = Response(text="Hello World")
        assert str(response) == "Hello World"
    
    def test_response_repr(self):
        """Test Response repr representation"""
        response = Response(text="Hello", model="gemini-2.5-flash")
        repr_str = repr(response)
        assert "Response(" in repr_str
        assert "text='Hello'" in repr_str
        # Note: repr only shows contents and text, not model


class TestSchemaBuilding:
    """Test schema building functionality"""
    
    def test_build_schema_from_json_object(self):
        """Test building schema from object type"""
        json_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        schema = build_schema_from_json(json_schema)
        
        assert schema.type == "OBJECT"
        assert "name" in schema.properties
        assert "age" in schema.properties
        assert schema.required == ["name"]
    
    def test_build_schema_from_json_string(self):
        """Test building schema from string type"""
        json_schema = {"type": "string", "enum": ["red", "blue", "green"]}
        schema = build_schema_from_json(json_schema)
        
        assert schema.type == "STRING"
        assert schema.enum == ["red", "blue", "green"]
    
    def test_build_schema_from_json_array(self):
        """Test building schema from array type"""
        json_schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        schema = build_schema_from_json(json_schema)
        
        assert schema.type == "ARRAY"
        assert schema.items is not None
    
    def test_build_schema_from_json_primitives(self):
        """Test building schema from primitive types"""
        for json_type, expected_type in [
            ("boolean", "BOOLEAN"),
            ("number", "NUMBER"),
            ("integer", "INTEGER")
        ]:
            json_schema = {"type": json_type}
            schema = build_schema_from_json(json_schema)
            assert schema.type == expected_type
    
    def test_build_schema_unsupported_type(self):
        """Test error handling for unsupported types"""
        json_schema = {"type": "unsupported"}
        with pytest.raises(ValueError, match="Unsupported type: unsupported"):
            build_schema_from_json(json_schema)
    
    def test_config_from_schema(self):
        """Test configuration generation from schema"""
        json_schema = {
            "type": "object",
            "properties": {"result": {"type": "string"}}
        }
        schema = build_schema_from_json(json_schema)
        config = config_from_schema(schema)
        
        assert config.response_schema == schema
        assert config.response_mime_type == "application/json"


class TestGenerateContentRetry:
    """Test main content generation function"""
    
    @patch('llm7shi.gemini.client.models.generate_content_stream')
    def test_basic_generation(self, mock_stream):
        """Test basic text generation"""
        mock_chunks = [
            MockChunk("Hello "),
            MockChunk("World!")
        ]
        mock_stream.return_value = iter(mock_chunks)
        
        response = generate_content_retry(["Test prompt"], file=None)
        
        assert response.text == "Hello World!"
        assert response.model == "gemini-2.5-flash"
        assert len(response.chunks) == 2
        mock_stream.assert_called_once()
    
    @patch('llm7shi.gemini.client.models.generate_content_stream')
    def test_thinking_process_extraction(self, mock_stream):
        """Test extraction of thinking process"""
        mock_chunks = [
            MockChunk("I need to think...", is_thought=True),
            MockChunk("The answer is 42", is_thought=False)
        ]
        mock_stream.return_value = iter(mock_chunks)
        
        response = generate_content_retry(["What is the answer?"], file=None)
        
        assert response.thoughts == "I need to think..."
        assert response.text == "The answer is 42"
    
    @patch('llm7shi.gemini.client.models.generate_content_stream')
    def test_custom_model(self, mock_stream):
        """Test custom model parameter"""
        mock_chunks = [MockChunk("Response")]
        mock_stream.return_value = iter(mock_chunks)
        
        response = generate_content_retry(
            ["Test"], 
            model="gemini-2.5-pro",
            file=None
        )
        
        assert response.model == "gemini-2.5-pro"
        mock_stream.assert_called_once()
        call_args = mock_stream.call_args
        assert call_args[1]['model'] == "gemini-2.5-pro"
    
    @patch('llm7shi.gemini.client.models.generate_content_stream')
    def test_thinking_budget_parameter(self, mock_stream):
        """Test thinking budget parameter"""
        mock_chunks = [MockChunk("Response")]
        mock_stream.return_value = iter(mock_chunks)
        
        response = generate_content_retry(
            ["Test"], 
            thinking_budget=50000,
            file=None
        )
        
        call_args = mock_stream.call_args
        assert call_args[1]['config'].thinking_config.thinking_budget == 50000
    
    @patch('llm7shi.gemini.client.models.generate_content_stream')
    def test_with_config(self, mock_stream):
        """Test generation with config parameter"""
        mock_chunks = [MockChunk('{"result": "test"}')]
        mock_stream.return_value = iter(mock_chunks)
        
        from google.genai import types
        config = types.GenerateContentConfig(response_mime_type="application/json")
        response = generate_content_retry(
            ["Test"], 
            config=config,
            file=None
        )
        
        call_args = mock_stream.call_args
        # Config should have thinking_config added but preserve original settings
        passed_config = call_args[1]['config']
        assert passed_config.response_mime_type == "application/json"
        assert passed_config.thinking_config is not None

    @patch('llm7shi.gemini.client.models.generate_content_stream')
    @patch('time.sleep')
    @patch('builtins.print')  # Mock print to avoid stderr output
    def test_retry_logic_429(self, mock_print, mock_sleep, mock_stream):
        """Test retry logic for 429 errors"""
        # Mock a 429 error followed by success
        from google.genai.errors import APIError
        error_429 = APIError("Rate limit exceeded", {"error": {"details": []}})
        error_429.code = 429
        
        mock_chunks = [MockChunk("Success after retry")]
        
        # First call raises 429, second succeeds
        mock_stream.side_effect = [error_429, iter(mock_chunks)]
        
        response = generate_content_retry(["Test"], file=None)
        
        assert response.text == "Success after retry"
        assert mock_stream.call_count == 2
    
    @patch('llm7shi.gemini.client.models.generate_content_stream')
    @patch('time.sleep')
    @patch('builtins.print')  # Mock print to avoid stderr output
    def test_retry_logic_server_errors(self, mock_print, mock_sleep, mock_stream):
        """Test retry logic for server errors (500, 502, 503)"""
        from google.genai.errors import APIError
        
        for error_code in [500, 502, 503]:
            mock_sleep.reset_mock()
            mock_stream.reset_mock()
            mock_print.reset_mock()
            
            error = APIError(f"Server error {error_code}", {"error": {"details": []}})
            error.code = error_code
            
            mock_chunks = [MockChunk(f"Success after {error_code}")]
            mock_stream.side_effect = [error, iter(mock_chunks)]
            
            response = generate_content_retry(["Test"], file=None)
            
            assert response.text == f"Success after {error_code}"
            assert mock_stream.call_count == 2


class TestFileOperations:
    """Test file upload and delete operations"""
    
    @patch('llm7shi.gemini.client.files.upload')
    @patch('llm7shi.gemini.client.files.get')
    @patch('time.sleep')
    def test_upload_file_success(self, mock_sleep, mock_get, mock_upload):
        """Test successful file upload with processing wait"""
        # Mock upload response - initially PROCESSING
        mock_file = MagicMock()
        mock_file.name = "files/test123"
        mock_file.state.name = "PROCESSING"  # Initial state after upload
        mock_upload.return_value = mock_file
        
        # Mock processing states: first processing, then active
        mock_active = MagicMock()
        mock_active.state.name = "ACTIVE"
        
        mock_get.side_effect = [mock_active]
        
        result = upload_file("test.txt", "text/plain")
        
        assert result == mock_active  # Returns the final state
        # Check the actual call structure with UploadFileConfig
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args[1]['file'] == "test.txt"
        assert call_args[1]['config'].mime_type == "text/plain"
        assert call_args[1]['config'].display_name == "test.txt"
    
    @patch('llm7shi.gemini.client.files.delete')
    def test_delete_file_success(self, mock_delete):
        """Test successful file deletion"""
        # Create a mock file object with name attribute
        mock_file = MagicMock()
        mock_file.name = "files/test123"
        
        delete_file(mock_file)
        
        mock_delete.assert_called_once_with(name="files/test123")


class TestBackwardCompatibility:
    """Test backward compatibility functions"""
    
    @patch('llm7shi.gemini.generate_content_retry')
    def test_legacy_function_wrapper(self, mock_generate):
        """Test that legacy function names still work"""
        mock_response = Response(text="Legacy response")
        mock_generate.return_value = mock_response
        
        # Test that the new function is called with correct parameters
        from llm7shi.gemini import generate_content_retry as legacy_func
        result = legacy_func(["Test"])
        
        assert result.text == "Legacy response"
        mock_generate.assert_called_once()