import pytest
from unittest.mock import patch

# Set dummy API keys for all tests
import os
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["OPENAI_API_KEY"] = "dummy"

from llm7shi.compat import generate_with_schema


class TestVendorPrefixSelection:
    """Test vendor prefix model selection logic"""
    
    @patch('llm7shi.compat._generate_with_openai')
    def test_openai_vendor_prefix(self, mock_openai):
        """Test OpenAI vendor prefix routing"""
        mock_openai.return_value = "prefix_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="openai:gpt-4o-mini"
        )
        
        assert result == "prefix_response"
        mock_openai.assert_called_once()
        # Check that vendor prefix was removed
        call_args = mock_openai.call_args
        assert call_args[0][0] == "gpt-4o-mini"
    
    @patch('llm7shi.compat._generate_with_gemini')
    def test_google_vendor_prefix(self, mock_gemini):
        """Test Google vendor prefix routing"""
        mock_gemini.return_value = "google_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="google:gemini-2.5-flash"
        )
        
        assert result == "google_response"
        mock_gemini.assert_called_once()
        # Check that vendor prefix was removed
        call_args = mock_gemini.call_args
        assert call_args[0][0] == "gemini-2.5-flash"
    
    @patch('llm7shi.compat._generate_with_openai')
    def test_empty_openai_prefix(self, mock_openai):
        """Test empty OpenAI prefix uses default model"""
        mock_openai.return_value = "empty_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="openai:"
        )
        
        assert result == "empty_response"
        mock_openai.assert_called_once()
        # Check that empty string was passed (will use default model)
        call_args = mock_openai.call_args
        assert call_args[0][0] == ""
    
    @patch('llm7shi.compat._generate_with_gemini')
    def test_empty_google_prefix(self, mock_gemini):
        """Test empty Google prefix uses default model"""
        mock_gemini.return_value = "empty_google_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="google:"
        )
        
        assert result == "empty_google_response"
        mock_gemini.assert_called_once()
        # Check that empty string was passed (will use default model)
        call_args = mock_gemini.call_args
        assert call_args[0][0] == ""
    
    def test_unsupported_vendor_prefix(self):
        """Test unsupported vendor prefix raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported vendor prefix: unknown"):
            generate_with_schema(
                contents=["Test"],
                model="unknown:some-model"
            )
    
    @patch('llm7shi.compat._generate_with_gemini')
    def test_backward_compatibility_gemini(self, mock_gemini):
        """Test backward compatibility for gemini models without prefix"""
        mock_gemini.return_value = "compat_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="gemini-2.5-flash"
        )
        
        assert result == "compat_response"
        mock_gemini.assert_called_once()
        call_args = mock_gemini.call_args
        assert call_args[0][0] == "gemini-2.5-flash"
    
    @patch('llm7shi.compat._generate_with_openai')
    def test_backward_compatibility_openai(self, mock_openai):
        """Test backward compatibility for non-gemini models without prefix"""
        mock_openai.return_value = "compat_openai_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="gpt-4o-mini"
        )
        
        assert result == "compat_openai_response"
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        assert call_args[0][0] == "gpt-4o-mini"
    
    @patch('llm7shi.compat._generate_with_openai')
    def test_unknown_model_defaults_to_openai(self, mock_openai):
        """Test unknown model name defaults to OpenAI"""
        mock_openai.return_value = "unknown_model_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="some-unknown-model"
        )
        
        assert result == "unknown_model_response"
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        assert call_args[0][0] == "some-unknown-model"