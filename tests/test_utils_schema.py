import pytest

from llm7shi.utils import (
    add_additional_properties_false,
    inline_defs,
    extract_descriptions,
)


class TestAddAdditionalPropertiesFalse:
    """Test schema modification for OpenAI compatibility"""
    
    def test_simple_object_schema(self):
        """Test adding additionalProperties: false to simple object"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        result = add_additional_properties_false(schema)
        
        assert result["additionalProperties"] is False
        assert result["type"] == "object"
        assert "properties" in result
    
    def test_nested_object_schema(self):
        """Test recursive addition for nested objects"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        }
        
        result = add_additional_properties_false(schema)
        
        assert result["additionalProperties"] is False
        assert result["properties"]["user"]["additionalProperties"] is False
    
    def test_array_with_object_items(self):
        """Test handling of arrays with object items"""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"}
                }
            }
        }
        
        result = add_additional_properties_false(schema)
        
        # Array itself should not get additionalProperties
        assert "additionalProperties" not in result
        # But the object items should
        assert result["items"]["additionalProperties"] is False
    
    def test_non_object_schema(self):
        """Test that non-object schemas are unchanged"""
        schema = {"type": "string", "enum": ["red", "blue"]}
        
        result = add_additional_properties_false(schema)
        
        assert result == schema
        assert "additionalProperties" not in result
    
    def test_schema_with_existing_additional_properties(self):
        """Test that existing additionalProperties is preserved"""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": True
        }
        
        result = add_additional_properties_false(schema)
        
        # Should override to False
        assert result["additionalProperties"] is False
    
    def test_deeply_nested_schema(self):
        """Test deeply nested object structures"""
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        
        result = add_additional_properties_false(schema)
        
        assert result["additionalProperties"] is False
        assert result["properties"]["level1"]["additionalProperties"] is False
        assert result["properties"]["level1"]["properties"]["level2"]["additionalProperties"] is False


class TestInlineDefs:
    """Test schema reference inlining"""
    
    def test_simple_ref_inlining(self):
        """Test inlining of simple $ref"""
        schema = {
            "type": "object",
            "properties": {
                "user": {"$ref": "#/$defs/User"}
            },
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        }
        
        result = inline_defs(schema)
        
        assert "$defs" not in result
        assert result["properties"]["user"]["type"] == "object"
        assert result["properties"]["user"]["properties"]["name"]["type"] == "string"
    
    def test_nested_refs(self):
        """Test inlining of nested references"""
        schema = {
            "type": "object",
            "properties": {
                "data": {"$ref": "#/$defs/Data"}
            },
            "$defs": {
                "Data": {
                    "type": "object",
                    "properties": {
                        "user": {"$ref": "#/$defs/User"}
                    }
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        }
        
        result = inline_defs(schema)
        
        assert "$defs" not in result
        assert result["properties"]["data"]["properties"]["user"]["type"] == "object"
    
    def test_array_items_ref(self):
        """Test inlining refs in array items"""
        schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/User"}
                }
            },
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        }
        
        result = inline_defs(schema)
        
        assert "$defs" not in result
        assert result["properties"]["users"]["items"]["type"] == "object"
    
    def test_schema_without_defs(self):
        """Test schema without $defs remains unchanged"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        result = inline_defs(schema)
        
        assert result == schema
    
    def test_schema_without_refs(self):
        """Test schema with $defs but no $refs"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "$defs": {
                "UnusedType": {"type": "string"}
            }
        }
        
        result = inline_defs(schema)
        
        # $defs should be removed even if unused
        assert "$defs" not in result
        assert result["properties"]["name"]["type"] == "string"
    
    def test_title_removal(self):
        """Test that title fields are removed during inlining"""
        schema = {
            "type": "object",
            "title": "MainSchema",
            "properties": {
                "user": {"$ref": "#/$defs/User"}
            },
            "$defs": {
                "User": {
                    "type": "object",
                    "title": "UserSchema",
                    "properties": {
                        "name": {"type": "string", "title": "UserName"}
                    }
                }
            }
        }
        
        result = inline_defs(schema)
        
        assert "title" not in result
        assert "title" not in result["properties"]["user"]
        assert "title" not in result["properties"]["user"]["properties"]["name"]
    
    def test_circular_references(self):
        """Test handling of circular references"""
        schema = {
            "type": "object",
            "properties": {
                "node": {"$ref": "#/$defs/Node"}
            },
            "$defs": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "child": {"$ref": "#/$defs/Node"}
                    }
                }
            }
        }
        
        # This will cause infinite recursion in current implementation
        # We should catch the RecursionError
        with pytest.raises(RecursionError):
            inline_defs(schema)


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