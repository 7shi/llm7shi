import os
import pytest
from unittest.mock import patch, MagicMock
from typing import List
from pydantic import BaseModel, Field
from llm7shi import config_from_schema, generate_content_retry


class LocationTemperature(BaseModel):
    location: str
    temperature: float = Field(description="Temperature in Celsius")


class LocationsAndTemperatures(BaseModel):
    locations_and_temperatures: List[LocationTemperature]


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
def test_schema2_example(mock_stream):
    """Test schema2.py example functionality"""
    # Mock JSON response
    json_response = '{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]}'
    mock_chunks = [
        MockChunk('{"locations_and_temperatures": '),
        MockChunk('[{"location": "Tokyo", '),
        MockChunk('"temperature": 32.22}]}')
    ]
    mock_stream.return_value = iter(mock_chunks)
    
    # Test direct Pydantic model usage (as in schema2.py)
    response = generate_content_retry(
        ["The temperature in Tokyo is 90 degrees Fahrenheit."],
        config=config_from_schema(LocationsAndTemperatures),
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
    
    # Verify call arguments
    call_args = mock_stream.call_args
    assert call_args[1]['contents'] == ["The temperature in Tokyo is 90 degrees Fahrenheit."]
    assert call_args[1]['model'] == "gemini-2.5-flash"
    
    # Test that the response can be parsed with Pydantic
    parsed_result = LocationsAndTemperatures.model_validate_json(response.text)
    assert len(parsed_result.locations_and_temperatures) == 1
    assert parsed_result.locations_and_temperatures[0].location == "Tokyo"
    assert parsed_result.locations_and_temperatures[0].temperature == 32.22


def test_pydantic_model_schema_generation():
    """Test that Pydantic models work with config_from_schema"""
    # Test that config_from_schema accepts Pydantic models directly
    config = config_from_schema(LocationsAndTemperatures)
    assert config is not None
    
    # Test individual model
    config_single = config_from_schema(LocationTemperature)
    assert config_single is not None


def test_pydantic_model_validation():
    """Test Pydantic model validation"""
    # Valid data
    valid_data = {
        "location": "Tokyo", 
        "temperature": 32.22
    }
    location_temp = LocationTemperature(**valid_data)
    assert location_temp.location == "Tokyo"
    assert location_temp.temperature == 32.22
    
    # Valid nested data
    valid_nested = {
        "locations_and_temperatures": [
            {"location": "Tokyo", "temperature": 32.22},
            {"location": "Paris", "temperature": 25.0}
        ]
    }
    locations = LocationsAndTemperatures(**valid_nested)
    assert len(locations.locations_and_temperatures) == 2
    assert locations.locations_and_temperatures[0].location == "Tokyo"
    assert locations.locations_and_temperatures[1].location == "Paris"
    
    # Test JSON parsing
    json_str = '{"locations_and_temperatures": [{"location": "Tokyo", "temperature": 32.22}]}'
    parsed = LocationsAndTemperatures.model_validate_json(json_str)
    assert len(parsed.locations_and_temperatures) == 1
    assert parsed.locations_and_temperatures[0].location == "Tokyo"


def test_pydantic_field_description():
    """Test that Field descriptions are preserved"""
    # Check that the description is accessible
    field_info = LocationTemperature.model_fields['temperature']
    assert field_info.description == "Temperature in Celsius"