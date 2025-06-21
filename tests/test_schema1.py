import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from llm7shi import build_schema_from_json, config_from_schema, generate_content_retry


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


@pytest.fixture
def schema1_json():
    """Load schema1.json for testing"""
    schema_path = Path(__file__).parent.parent / "examples" / "schema1.json"
    with open(schema_path) as f:
        return json.load(f)


@patch('llm7shi.gemini.client.models.generate_content_stream')
def test_schema1_example(mock_stream, schema1_json):
    """Test schema1.py example functionality"""
    # Mock JSON response
    json_response = '{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]}'
    mock_chunks = [
        MockChunk('{"locations_and_temperatures": '),
        MockChunk('[{"location": "Tokyo", '),
        MockChunk('"temperature": 32.22}]}')
    ]
    mock_stream.return_value = iter(mock_chunks)
    
    # Test schema loading and validation
    schema = build_schema_from_json(schema1_json)
    assert schema is not None
    
    # Test config creation
    config = config_from_schema(schema)
    assert config is not None
    
    # Test the generate_content_retry call from schema1.py
    response = generate_content_retry(
        ["The temperature in Tokyo is 90 degrees Fahrenheit."],
        config=config,
        file=None
    )
    
    # Verify the call was made
    mock_stream.assert_called_once()
    
    # Check response structure
    assert hasattr(response, 'text')
    assert hasattr(response, 'thoughts')
    assert hasattr(response, 'model')
    assert hasattr(response, 'chunks')
    assert hasattr(response, 'config')
    
    # Verify response content
    expected_text = '{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]}'
    assert response.text == expected_text
    assert response.model == "gemini-2.5-flash"
    assert len(response.chunks) == 3
    assert response.config == config
    
    # Verify call arguments
    call_args = mock_stream.call_args
    assert call_args[1]['contents'] == ["The temperature in Tokyo is 90 degrees Fahrenheit."]
    assert call_args[1]['model'] == "gemini-2.5-flash"
    assert call_args[1]['config'] == config


def test_schema1_direct_json_usage(schema1_json):
    """Test that schema1 works with direct JSON usage (without build_schema_from_json)"""
    # Test that config_from_schema accepts raw JSON dict
    config = config_from_schema(schema1_json)
    assert config is not None
    
    # This should work without validation (as mentioned in the comments)
    with patch('llm7shi.gemini.client.models.generate_content_stream') as mock_stream:
        mock_chunks = [MockChunk('{"test": "response"}')]
        mock_stream.return_value = iter(mock_chunks)
        
        response = generate_content_retry(
            ["Test input"],
            config=config,
            file=None
        )
        
        assert response.text == '{"test": "response"}'
        mock_stream.assert_called_once()


def test_schema1_validation():
    """Test that build_schema_from_json provides validation"""
    # Valid schema should work
    valid_schema = {
        "type": "object",
        "properties": {
            "test": {"type": "string"}
        }
    }
    schema = build_schema_from_json(valid_schema)
    assert schema is not None
    
    # Invalid schema should raise an error
    invalid_schema = {
        "type": "invalid_type",
        "properties": {}
    }
    with pytest.raises(ValueError, match="Unsupported type"):
        build_schema_from_json(invalid_schema)