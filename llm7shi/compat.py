import json
import sys
import inspect
import re
from typing import Dict, Any, List, Union, Type
from pydantic import BaseModel

from .utils import contents_to_openai_messages, add_additional_properties_false, do_show_params, inline_defs
from .response import Response
from .terminal import MarkdownStreamConverter
from .monitor import StreamMonitor

# Vendor prefixes for examples (use vendor prefix only for easier maintenance)
VENDOR_PREFIXES = ["google:", "openai:", "ollama:"]

# OpenAI-compatible vendor configurations
OPENAI_COMPATIBLE_VENDORS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "default_model": "google/gemma-3-4b-it:free",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "default_model": "llama-3.1-8b-instant",
    },
    "grok": {
        "base_url": "https://api.x.ai/v1",
        "api_key_env": "XAI_API_KEY",
        "default_model": "grok-4-1-fast-non-reasoning",
    },
}

# Type alias for message content
MessageContent = Union[List[str], List[Dict[str, str]]]


def generate_with_schema(
    contents: MessageContent,
    schema: Union[Dict[str, Any], Type[BaseModel], None] = None,
    *,
    model: str = "",
    temperature: float = None,
    system_prompt: str = None,
    include_thoughts: bool = True,
    thinking_budget=None,
    file=sys.stdout,
    show_params: bool = True,
    max_length=None,
    check_repetition: bool = True,
) -> Response:
    """Generate content using OpenAI, Gemini, or Ollama API.

    Args:
        contents: List of user content strings OR OpenAI message format
        schema: JSON schema for structured output, Pydantic model, or None for plain text
        model: Model name with optional vendor prefix (e.g., "openai:gpt-4.1-mini", "google:gemini-2.5-flash", "ollama:qwen3:4b"). Defaults to Gemini.
        temperature: Temperature parameter for generation (None = use model default)
        system_prompt: System prompt as string
        include_thoughts: Whether to include thinking process (Gemini and Ollama only)
        thinking_budget: Optional thinking budget (Gemini only)
        file: File to stream output to. Defaults to sys.stdout.
        show_params: Whether to display parameters before generation
        max_length: Maximum length of generated text (default: None, no limit)
        check_repetition: Whether to check for repetitive patterns (default: True)

    Returns:
        Response: Response object containing generated text and metadata
    """
    # Parse vendor prefix from model name
    actual_model = model
    vendor_prefix = "google"  # default to Google

    if model:
        # Check for vendor prefix using regex
        vendor_match = re.match(r"([^:]+):(.*)", model)
        if vendor_match:
            vendor_prefix = vendor_match.group(1)
            actual_model = vendor_match.group(2)
        else:
            # No vendor prefix - check for backward compatibility patterns
            if model.startswith("gemini"):
                # Backward compatibility: gemini models use Gemini
                pass
            else:
                vendor_prefix = "openai"

    # Check if vendor is OpenAI-compatible (openrouter, groq, grok)
    if vendor_prefix in OPENAI_COMPATIBLE_VENDORS:
        vendor_config = OPENAI_COMPATIBLE_VENDORS[vendor_prefix]

        # Use default model if actual_model is empty
        if not actual_model:
            actual_model = vendor_config["default_model"]

        # Only add base_url if not already specified by user
        if "@" not in actual_model:
            # Construct model string with vendor defaults
            actual_model = f"{actual_model}@{vendor_config['base_url']}|{vendor_config['api_key_env']}"

        return _generate_with_openai(actual_model, contents, schema, temperature, system_prompt, file, show_params, max_length, check_repetition)

    elif vendor_prefix == "google":
        return _generate_with_gemini(actual_model, contents, schema, temperature, system_prompt, include_thoughts, thinking_budget, file, show_params, max_length, check_repetition)
    elif vendor_prefix == "openai":
        return _generate_with_openai(actual_model, contents, schema, temperature, system_prompt, file, show_params, max_length, check_repetition)
    elif vendor_prefix == "ollama":
        return _generate_with_ollama(actual_model, contents, schema, temperature, system_prompt, include_thoughts, file, show_params, max_length, check_repetition)
    else:
        raise ValueError(f"Unsupported vendor prefix: {vendor_prefix}")


def _generate_with_gemini(
    model: str,
    contents: MessageContent,
    schema: Union[Dict[str, Any], Type[BaseModel], None],
    temperature: float = None,
    system_prompt: str = None,
    include_thoughts: bool = True,
    thinking_budget=None,
    file=sys.stdout,
    show_params: bool = True,
    max_length=None,
    check_repetition: bool = True,
) -> Response:
    """Generate with Gemini API."""
    from . import config_from_schema, generate_content_retry, config_text, DEFAULT_MODEL
    from .utils import is_openai_messages, openai_messages_to_contents

    # Convert to Gemini format if needed
    if is_openai_messages(contents):
        # Convert OpenAI message format to Gemini Content objects and extract system prompt
        gemini_contents, message_system_prompt = openai_messages_to_contents(contents)

        # Check for conflict between message-embedded and parameter system prompts
        if message_system_prompt and system_prompt:
            raise ValueError(
                "System prompt provided in both messages (role='system') and system_prompt parameter. "
                "Please use only one method."
            )

        # Use message-embedded system prompt if present, otherwise use parameter
        final_system_prompt = message_system_prompt or system_prompt
    else:
        # Legacy List[str] format
        gemini_contents = contents
        final_system_prompt = system_prompt

    # Build config from schema or use text config
    if schema is not None:
        generate_content_config = config_from_schema(schema)
    else:
        generate_content_config = config_text

    if temperature is not None:
        generate_content_config.temperature = temperature
    if final_system_prompt:
        generate_content_config.system_instruction = [final_system_prompt]

    # Display parameters if requested
    if show_params and file is not None:
        do_show_params(contents, model=(model or DEFAULT_MODEL), file=file)

    # Generate content
    result = generate_content_retry(
        model=model,
        config=generate_content_config,
        contents=gemini_contents,
        show_params=False,
        include_thoughts=include_thoughts,
        thinking_budget=thinking_budget,
        file=file,
        max_length=max_length,
        check_repetition=check_repetition
    )

    # Return Response object
    return result


def _generate_with_openai(
    model: str,
    contents: MessageContent,
    schema: Union[Dict[str, Any], Type[BaseModel], None],
    temperature: float = None,
    system_prompt: str = None,
    file=sys.stdout,
    show_params: bool = True,
    max_length=None,
    check_repetition: bool = True,
) -> Response:
    """Generate with OpenAI API with streaming."""
    from .openai import DEFAULT_MODEL, generate_content

    # Extract base_url and api_key_env from model if present
    # Format: model@base_url|api_key_env
    base_url = None
    api_key_env = None
    if model and "@" in model:
        model, url_rest = model.rsplit("@", 1)
        # Check for api_key_env specification
        if "|" in url_rest:
            base_url, api_key_env = url_rest.split("|", 1)
        else:
            base_url = url_rest

    # Build kwargs for OpenAI API
    kwargs = {}
    
    if schema is not None:
        # Convert Pydantic model to JSON schema
        if inspect.isclass(schema) and issubclass(schema, BaseModel):
            schema = schema.model_json_schema()
            schema = inline_defs(schema)  # Inline $defs references
        
        # Adjust JSON schema
        schema_for_openai = add_additional_properties_false(schema)
        
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "evaluation_response",
                "schema": schema_for_openai,
                "strict": True
            }
        }
    
    # Add temperature only if provided
    if temperature is not None:
        kwargs["temperature"] = temperature

    # Convert contents to OpenAI format messages
    openai_messages = contents_to_openai_messages(contents, system_prompt)

    # Display parameters if requested
    if show_params and file is not None:
        do_show_params(contents, model=(model or DEFAULT_MODEL), file=file)

    return generate_content(
        model=model,
        messages=openai_messages,
        file=file,
        max_length=max_length,
        check_repetition=check_repetition,
        base_url=base_url,
        api_key_env=api_key_env,
        **kwargs
    )


def _generate_with_ollama(
    model: str,
    contents: MessageContent,
    schema: Union[Dict[str, Any], Type[BaseModel], None],
    temperature: float = None,
    system_prompt: str = None,
    include_thoughts: bool = True,
    file=sys.stdout,
    show_params: bool = True,
    max_length=None,
    check_repetition: bool = True,
) -> Response:
    """Generate with Ollama API with streaming."""
    from .ollama import DEFAULT_MODEL, generate_content
    
    # Build kwargs for Ollama API
    kwargs = {}
    
    if schema is not None:
        # Convert Pydantic model to JSON schema
        if inspect.isclass(schema) and issubclass(schema, BaseModel):
            schema = schema.model_json_schema()
        
        kwargs["format"] = schema
    
    # Add temperature only if provided
    if temperature is not None:
        kwargs["options"] = {"temperature": temperature}

    # Convert contents to OpenAI format messages (Ollama uses similar format)
    ollama_messages = contents_to_openai_messages(contents, system_prompt)

    # Display parameters if requested
    if show_params and file is not None:
        do_show_params(contents, model=(model or DEFAULT_MODEL), file=file)
    
    return generate_content(
        model=model,
        messages=ollama_messages,
        think=include_thoughts,
        file=file,
        max_length=max_length,
        check_repetition=check_repetition,
        **kwargs
    )
