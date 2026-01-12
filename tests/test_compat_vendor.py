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
            model="openai:gpt-4.1-mini"
        )
        
        assert result == "prefix_response"
        mock_openai.assert_called_once()
        # Check that vendor prefix was removed
        call_args = mock_openai.call_args
        assert call_args[0][0] == "gpt-4.1-mini"
    
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
    
    @patch('llm7shi.compat._generate_with_ollama')
    def test_ollama_vendor_prefix(self, mock_ollama):
        """Test Ollama vendor prefix routing"""
        mock_ollama.return_value = "ollama_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="ollama:qwen3:4b"
        )
        
        assert result == "ollama_response"
        mock_ollama.assert_called_once()
        # Check that vendor prefix was removed
        call_args = mock_ollama.call_args
        assert call_args[0][0] == "qwen3:4b"
    
    @patch('llm7shi.compat._generate_with_ollama')
    def test_empty_ollama_prefix(self, mock_ollama):
        """Test empty Ollama prefix uses default model"""
        mock_ollama.return_value = "empty_ollama_response"
        
        result = generate_with_schema(
            contents=["Test"],
            model="ollama:"
        )
        
        assert result == "empty_ollama_response"
        mock_ollama.assert_called_once()
        # Check that empty string was passed (will use default model)
        call_args = mock_ollama.call_args
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
            model="gpt-4.1-mini"
        )
        
        assert result == "compat_openai_response"
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        assert call_args[0][0] == "gpt-4.1-mini"
    
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


class TestBaseUrlAndApiKeyEnvParsing:
    """Test base_url and api_key_env parsing from model string"""

    @patch('llm7shi.openai.generate_content')
    def test_model_with_base_url_only(self, mock_generate):
        """Test model@base_url syntax without api_key_env"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openai:gpt-4@http://localhost:8080/v1"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that base_url was extracted and api_key_env is None
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["base_url"] == "http://localhost:8080/v1"
        assert call_kwargs["api_key_env"] is None

        # Check that model name was cleaned
        assert mock_generate.call_args.kwargs["model"] == "gpt-4"

    @patch('llm7shi.openai.generate_content')
    def test_model_with_base_url_and_api_key_env(self, mock_generate):
        """Test model@base_url|api_key_env syntax"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openai:gpt-4@http://localhost:8080/v1|MY_API_KEY"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that both base_url and api_key_env were extracted
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["base_url"] == "http://localhost:8080/v1"
        assert call_kwargs["api_key_env"] == "MY_API_KEY"

        # Check that model name was cleaned
        assert mock_generate.call_args.kwargs["model"] == "gpt-4"

    @patch('llm7shi.openai.generate_content')
    def test_model_without_base_url(self, mock_generate):
        """Test model without @base_url syntax"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openai:gpt-4.1-mini"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that base_url and api_key_env are None
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["base_url"] is None
        assert call_kwargs["api_key_env"] is None

        # Check that model name was preserved
        assert mock_generate.call_args.kwargs["model"] == "gpt-4.1-mini"

    @patch('llm7shi.openai.generate_content')
    def test_base_url_with_port(self, mock_generate):
        """Test base_url with port number (colon in URL)"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openai:llama.cpp/gpt-oss@http://192.168.0.8:8080/v1|CUSTOM_KEY"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that URL with port was parsed correctly
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["base_url"] == "http://192.168.0.8:8080/v1"
        assert call_kwargs["api_key_env"] == "CUSTOM_KEY"
        assert mock_generate.call_args.kwargs["model"] == "llama.cpp/gpt-oss"

    @patch('llm7shi.openai.generate_content')
    def test_empty_api_key_env(self, mock_generate):
        """Test model@base_url| with empty api_key_env"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openai:gpt-4@http://localhost:8080/v1|"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that empty string api_key_env was extracted
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["base_url"] == "http://localhost:8080/v1"
        assert call_kwargs["api_key_env"] == ""

    @patch('llm7shi.openai.generate_content')
    def test_api_key_env_with_underscores(self, mock_generate):
        """Test api_key_env with underscores and numbers"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openai:gpt-4@http://localhost:8080/v1|MY_CUSTOM_API_KEY_123"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that api_key_env with special characters was parsed
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["api_key_env"] == "MY_CUSTOM_API_KEY_123"


class TestOpenAICompatibleVendors:
    """Test OpenAI-compatible vendor prefixes (openrouter, groq, grok)"""

    @patch('llm7shi.openai.generate_content')
    def test_openrouter_with_default_model(self, mock_generate):
        """Test openrouter: prefix uses default model"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openrouter:"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that default model and vendor config were applied
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["model"] == "qwen/qwen3-4b:free"
        assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"
        assert call_kwargs["api_key_env"] == "OPENROUTER_API_KEY"

    @patch('llm7shi.openai.generate_content')
    def test_openrouter_with_specific_model(self, mock_generate):
        """Test openrouter: prefix with specific model"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openrouter:anthropic/claude-3.5-sonnet"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that vendor config was applied to specified model
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["model"] == "anthropic/claude-3.5-sonnet"
        assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"
        assert call_kwargs["api_key_env"] == "OPENROUTER_API_KEY"

    @patch('llm7shi.openai.generate_content')
    def test_groq_vendor_prefix(self, mock_generate):
        """Test groq: vendor prefix"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="groq:llama-3.3-70b-versatile"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that groq vendor config was applied
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["model"] == "llama-3.3-70b-versatile"
        assert call_kwargs["base_url"] == "https://api.groq.com/openai/v1"
        assert call_kwargs["api_key_env"] == "GROQ_API_KEY"

    @patch('llm7shi.openai.generate_content')
    def test_grok_vendor_prefix(self, mock_generate):
        """Test grok: vendor prefix"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="grok:grok-4-1"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that grok vendor config was applied
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["model"] == "grok-4-1"
        assert call_kwargs["base_url"] == "https://api.x.ai/v1"
        assert call_kwargs["api_key_env"] == "XAI_API_KEY"

    @patch('llm7shi.openai.generate_content')
    def test_openrouter_with_custom_url(self, mock_generate):
        """Test that user-specified @base_url is not overridden"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="openrouter:custom-model@http://custom-url/v1|MY_KEY"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that user's custom URL was preserved (no vendor defaults applied)
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["model"] == "custom-model"
        assert call_kwargs["base_url"] == "http://custom-url/v1"
        assert call_kwargs["api_key_env"] == "MY_KEY"

    @patch('llm7shi.openai.generate_content')
    def test_groq_default_model(self, mock_generate):
        """Test groq: prefix with empty model uses default"""
        mock_generate.return_value = "response"

        result = generate_with_schema(
            contents=["Test"],
            model="groq:"
        )

        assert result == "response"
        mock_generate.assert_called_once()

        # Check that default groq model was used
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["model"] == "llama-3.1-8b-instant"
        assert call_kwargs["base_url"] == "https://api.groq.com/openai/v1"
        assert call_kwargs["api_key_env"] == "GROQ_API_KEY"