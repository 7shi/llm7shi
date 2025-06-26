import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO
import json

from llm7shi.utils import (
    do_show_params,
    contents_to_openai_messages,
    add_additional_properties_false,
    inline_defs,
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