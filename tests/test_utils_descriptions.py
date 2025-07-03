import pytest
from pydantic import BaseModel, Field

from llm7shi.utils import extract_descriptions, create_json_descriptions_prompt


class TestExtractDescriptions:
    """Test description extraction from JSON schema"""
    
    def test_simple_property_descriptions(self):
        """Test extracting descriptions from simple properties"""
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "User's full name"
                },
                "age": {
                    "type": "integer",
                    "description": "User's age in years"
                }
            }
        }
        
        result = extract_descriptions(schema)
        
        assert result == {
            "name": "User's full name",
            "age": "User's age in years"
        }
    
    def test_nested_object_descriptions(self):
        """Test extracting descriptions from nested objects"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "description": "User information object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "User's name"
                        },
                        "email": {
                            "type": "string",
                            "description": "User's email address"
                        }
                    }
                }
            }
        }
        
        result = extract_descriptions(schema)
        
        assert result == {
            "user": "User information object",
            "name": "User's name",
            "email": "User's email address"
        }
    
    def test_array_item_descriptions(self):
        """Test extracting descriptions from array items"""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "description": "List of tags",
                    "items": {
                        "type": "string",
                        "description": "Individual tag"
                    }
                }
            }
        }
        
        result = extract_descriptions(schema)
        
        assert result == {
            "tags": "List of tags"
        }
    
    def test_properties_without_descriptions(self):
        """Test schema with properties that have no descriptions"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {
                    "type": "integer",
                    "description": "User's age"
                }
            }
        }
        
        result = extract_descriptions(schema)
        
        assert result == {"age": "User's age"}
    
    def test_empty_schema(self):
        """Test empty schema returns empty dict"""
        schema = {}
        
        result = extract_descriptions(schema)
        
        assert result == {}
    
    def test_schema_without_properties(self):
        """Test schema without properties section"""
        schema = {
            "type": "string",
            "description": "A simple string"
        }
        
        result = extract_descriptions(schema)
        
        assert result == {}
    
    def test_deeply_nested_descriptions(self):
        """Test deeply nested property descriptions"""
        schema = {
            "type": "object",
            "properties": {
                "company": {
                    "type": "object",
                    "description": "Company information",
                    "properties": {
                        "department": {
                            "type": "object",
                            "description": "Department details",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Department name"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        result = extract_descriptions(schema)
        
        assert result == {
            "company": "Company information",
            "department": "Department details",
            "name": "Department name"
        }


class TestCreateJsonDescriptionsPrompt:
    """Test JSON descriptions prompt generation"""
    
    def test_simple_json_schema(self):
        """Test prompt generation from simple JSON schema"""
        schema = {
            "type": "object",
            "properties": {
                "temperature": {
                    "type": "number",
                    "description": "Temperature in Celsius"
                },
                "location": {
                    "type": "string",
                    "description": "Geographic location name"
                }
            }
        }
        
        result = create_json_descriptions_prompt(schema)
        
        expected = "Please extract information to the following JSON fields.\n- temperature: Temperature in Celsius\n- location: Geographic location name"
        assert result == expected
    
    def test_pydantic_model_schema(self):
        """Test prompt generation from Pydantic model"""
        class LocationTemperature(BaseModel):
            reasoning: str
            location: str
            temperature: float = Field(description="Temperature in Celsius")
        
        result = create_json_descriptions_prompt(LocationTemperature)
        
        expected = "Please extract information to the following JSON fields.\n- temperature: Temperature in Celsius"
        assert result == expected
    
    def test_nested_pydantic_model(self):
        """Test prompt generation from nested Pydantic model"""
        class LocationTemperature(BaseModel):
            location: str
            temperature: float = Field(description="Temperature in Celsius")
        
        class WeatherData(BaseModel):
            source: str = Field(description="Data source name")
            locations_and_temperatures: list[LocationTemperature]
        
        result = create_json_descriptions_prompt(WeatherData)
        
        expected = "Please extract information to the following JSON fields.\n- source: Data source name\n- temperature: Temperature in Celsius"
        assert result == expected
    
    def test_schema_without_descriptions(self):
        """Test schema without descriptions returns empty string"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        result = create_json_descriptions_prompt(schema)
        
        assert result == ""
    
    def test_empty_schema(self):
        """Test empty schema returns empty string"""
        schema = {}
        
        result = create_json_descriptions_prompt(schema)
        
        assert result == ""
    
    def test_complex_nested_schema(self):
        """Test complex nested schema with multiple description levels"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "description": "User information",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "description": "User profile data",
                            "properties": {
                                "email": {
                                    "type": "string",
                                    "description": "Email address"
                                }
                            }
                        }
                    }
                },
                "timestamp": {
                    "type": "string",
                    "description": "Creation timestamp"
                }
            }
        }
        
        result = create_json_descriptions_prompt(schema)
        
        expected = "Please extract information to the following JSON fields.\n- user: User information\n- profile: User profile data\n- email: Email address\n- timestamp: Creation timestamp"
        assert result == expected
    
    def test_prompt_format_consistency(self):
        """Test that prompt format is consistent"""
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "User name"
                }
            }
        }
        
        result = create_json_descriptions_prompt(schema)
        
        # Check format structure
        lines = result.split('\n')
        assert lines[0] == "Please extract information to the following JSON fields."
        assert lines[1].startswith("- ")
        assert ": " in lines[1]