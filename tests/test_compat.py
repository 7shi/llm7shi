import pytest
from unittest.mock import patch, MagicMock
from typing import List
from pydantic import BaseModel, Field

# Set dummy API keys for all tests
import os
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["OPENAI_API_KEY"] = "dummy"

from llm7shi.compat import generate_with_schema


class LocationTemperature(BaseModel):
    """Test Pydantic model for temperature data"""
    location: str
    temperature: float = Field(description="Temperature in Celsius")


class LocationList(BaseModel):
    """Test Pydantic model for list of locations"""
    locations: List[LocationTemperature]


class TestModelSelection:
    """Test model selection logic"""
    
    @patch('llm7shi.compat._generate_with_gemini')
    def test_gemini_model_selection(self, mock_gemini):
        """Test that Gemini models are routed to Gemini function"""
        mock_gemini.return_value = "gemini_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="google:gemini-2.5-flash"
        )
        
        assert result == "gemini_response"
        mock_gemini.assert_called_once()
    
    @patch('llm7shi.compat._generate_with_openai')
    def test_openai_model_selection(self, mock_openai):
        """Test that OpenAI models are routed to OpenAI function"""
        mock_openai.return_value = "openai_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="openai:gpt-4o-mini"
        )
        
        assert result == "openai_response"
        mock_openai.assert_called_once()
    
    @patch('llm7shi.compat._generate_with_gemini')
    def test_default_model_selection(self, mock_gemini):
        """Test default model selection (should use Gemini)"""
        mock_gemini.return_value = "default_response"
        
        result = generate_with_schema(contents=["Test"])
        
        assert result == "default_response"
        mock_gemini.assert_called_once()
        # Check that default model ("") was passed
        call_args = mock_gemini.call_args
        assert call_args[0][0] == ""  # model parameter is first positional arg


class TestGeminiIntegration:
    """Test integration with Gemini API"""
    
    @patch('llm7shi.generate_content_retry')
    def test_basic_gemini_generation(self, mock_generate):
        """Test basic text generation with Gemini"""
        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_generate.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Hello World"],
            model="google:gemini-2.5-flash"
        )
        
        assert result.text == "Gemini response"
        mock_generate.assert_called_once()
    
    @patch('llm7shi.generate_content_retry')
    @patch('llm7shi.config_from_schema')
    def test_gemini_with_pydantic_schema(self, mock_config, mock_generate):
        """Test Gemini generation with Pydantic schema"""
        mock_config.return_value = {"response_schema": "test_schema"}
        mock_response = MagicMock()
        mock_response.text = '{"location": "Tokyo", "temperature": 25.0}'
        mock_generate.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Temperature in Tokyo"],
            schema=LocationTemperature,
            model="google:gemini-2.5-flash"
        )
        
        mock_config.assert_called_once()
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args[1]['config'] == {"response_schema": "test_schema"}
    
    @patch('llm7shi.generate_content_retry')
    @patch('llm7shi.config_from_schema')
    def test_gemini_with_json_schema(self, mock_config, mock_generate):
        """Test Gemini generation with JSON schema"""
        json_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        mock_config.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"name": "test"}'
        mock_generate.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Generate name"],
            schema=json_schema,
            model="google:gemini-2.5-flash"
        )
        
        mock_config.assert_called_once_with(json_schema)
        mock_generate.assert_called_once()
        assert result.text == '{"name": "test"}'
    
    @patch('llm7shi.generate_content_retry')
    def test_gemini_with_temperature(self, mock_generate):
        """Test Gemini generation with temperature parameter"""
        mock_response = MagicMock()
        mock_response.text = "Creative response"
        mock_generate.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Be creative"],
            temperature=0.9,
            model="google:gemini-2.5-flash"
        )
        
        call_args = mock_generate.call_args
        config = call_args[1]['config']
        assert config.temperature == 0.9
        assert result.text == "Creative response"
    
    @patch('llm7shi.generate_content_retry')
    def test_gemini_with_system_prompt(self, mock_generate):
        """Test Gemini generation with system prompt"""
        mock_response = MagicMock()
        mock_response.text = "Assistant response"
        mock_generate.return_value = mock_response
        
        result = generate_with_schema(
            contents=["User message"],
            system_prompt="You are helpful",
            model="google:gemini-2.5-flash"
        )
        
        call_args = mock_generate.call_args
        config = call_args[1]['config']
        assert config.system_instruction == ["You are helpful"]
        assert result.text == "Assistant response"


class TestOpenAIIntegration:
    """Test integration with OpenAI API"""
    
    @patch('llm7shi.openai.client')
    @patch('llm7shi.compat.contents_to_openai_messages')
    def test_basic_openai_generation(self, mock_messages, mock_client):
        """Test basic text generation with OpenAI"""
        mock_messages.return_value = [{"role": "user", "content": "Hello"}]
        
        # mock_client is already the mocked client object
        
        # Mock streaming response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        mock_chunk.choices[0].delta.content = "OpenAI response"
        mock_client.chat.completions.create.return_value = [mock_chunk]
        
        result = generate_with_schema(
            contents=["Hello World"],
            model="openai:gpt-4o-mini"
        )
        
        assert result.text == "OpenAI response"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('llm7shi.openai.client')
    @patch('llm7shi.compat.contents_to_openai_messages')
    @patch('llm7shi.compat.add_additional_properties_false')
    @patch('llm7shi.compat.inline_defs')
    def test_openai_with_pydantic_schema(self, mock_inline, mock_add_props, mock_messages, mock_client):
        """Test OpenAI generation with Pydantic schema"""
        mock_messages.return_value = [{"role": "user", "content": "Test"}]
        mock_add_props.return_value = {"processed": "schema"}
        mock_inline.return_value = {"final": "schema"}
        
        # mock_client is already the mocked client object
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = '{"location": "Tokyo", "temperature": 25}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Temperature data"],
            schema=LocationTemperature,
            model="openai:gpt-4o-mini"
        )
        
        # Verify schema processing pipeline
        mock_add_props.assert_called_once()
        mock_inline.assert_called_once()
        
        # Verify OpenAI API call
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['response_format']['json_schema']['schema'] == {"processed": "schema"}
    
    @patch('llm7shi.openai.client')
    @patch('llm7shi.compat.contents_to_openai_messages')
    @patch('llm7shi.compat.add_additional_properties_false')
    @patch('llm7shi.compat.inline_defs')
    def test_openai_with_json_schema(self, mock_inline, mock_add_props, mock_messages, mock_client):
        """Test OpenAI generation with JSON schema"""
        json_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        mock_messages.return_value = [{"role": "user", "content": "Test"}]
        mock_add_props.return_value = {"processed": "schema"}
        mock_inline.return_value = {"final": "schema"}
        
        # mock_client is already the mocked client object
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = '{"name": "test"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Generate name"],
            schema=json_schema,
            model="openai:gpt-4o-mini"
        )
        
        mock_add_props.assert_called_once_with(json_schema)
        # inline_defs is not called for non-Pydantic schemas in current implementation
    
    @patch('llm7shi.openai.client')
    @patch('llm7shi.compat.contents_to_openai_messages')
    def test_openai_with_temperature(self, mock_messages, mock_client):
        """Test OpenAI generation with temperature parameter"""
        mock_messages.return_value = [{"role": "user", "content": "Test"}]
        
        # mock_client is already the mocked client object
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Creative response"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Be creative"],
            temperature=0.8,
            model="openai:gpt-4o-mini"
        )
        
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.8
    
    @patch('llm7shi.openai.client')
    @patch('llm7shi.compat.contents_to_openai_messages')
    def test_openai_with_system_prompt(self, mock_messages, mock_client):
        """Test OpenAI generation with system prompt"""
        mock_messages.return_value = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        # mock_client is already the mocked client object
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "How can I help?"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generate_with_schema(
            contents=["Hello"],
            system_prompt="You are helpful",
            model="openai:gpt-4o-mini"
        )
        
        mock_messages.assert_called_with(["Hello"], "You are helpful")


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('llm7shi.openai.client')
    def test_openai_api_error(self, mock_client):
        """Test handling of OpenAI API errors"""
        # mock_client is already the mocked client object
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            generate_with_schema(
                contents=["Test"],
                model="openai:gpt-4o-mini"
            )
    
    @patch('llm7shi.openai.client')
    @patch('llm7shi.compat.contents_to_openai_messages')
    def test_unsupported_model(self, mock_messages, mock_client):
        """Test error handling for unsupported model names"""
        # Unsupported models go to OpenAI path, so mock it properly
        mock_messages.return_value = [{"role": "user", "content": "Test"}]
        
        # mock_client is already the mocked client object
        
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        mock_chunk.choices[0].delta.content = "fallback_response"
        mock_client.chat.completions.create.return_value = [mock_chunk]
        
        result = generate_with_schema(
            contents=["Test"],
            model="unsupported-model"
        )
        
        assert result.text == "fallback_response"


class TestSchemaProcessing:
    """Test schema processing utilities"""
    
    def test_pydantic_model_detection(self):
        """Test that Pydantic models are correctly identified"""
        with patch('llm7shi.compat._generate_with_gemini') as mock_gemini:
            mock_gemini.return_value = MagicMock()
            
            # Test with Pydantic model
            generate_with_schema(
                contents=["Test"],
                schema=LocationTemperature,
                model="google:gemini-2.5-flash"
            )
            
            # Should use config_from_schema path
            mock_gemini.assert_called_once()
    
    def test_json_schema_processing(self):
        """Test that JSON schemas are correctly processed"""
        with patch('llm7shi.compat._generate_with_gemini') as mock_gemini:
            mock_gemini.return_value = "test_result"
            
            json_schema = {"type": "object"}
            result = generate_with_schema(
                contents=["Test"],
                schema=json_schema,
                model="google:gemini-2.5-flash"
            )
            
            # Should call _generate_with_gemini once
            mock_gemini.assert_called_once()
            assert result == "test_result"
    
    def test_no_schema_provided(self):
        """Test generation without schema"""
        with patch('llm7shi.compat._generate_with_gemini') as mock_gemini:
            mock_gemini.return_value = MagicMock()
            
            generate_with_schema(
                contents=["Test"],
                model="google:gemini-2.5-flash"
            )
            
            call_args = mock_gemini.call_args
            # Should not pass config when no schema
            assert 'config' not in call_args[1] or call_args[1]['config'] is None
