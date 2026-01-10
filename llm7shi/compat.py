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


def generate_with_schema(
    contents: List[str],
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
        contents: List of user content strings
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
    
    if vendor_prefix == "google":
        return _generate_with_gemini(actual_model, contents, schema, temperature, system_prompt, include_thoughts, thinking_budget, file, show_params, max_length, check_repetition)
    elif vendor_prefix == "openai":
        return _generate_with_openai(actual_model, contents, schema, temperature, system_prompt, file, show_params, max_length, check_repetition)
    elif vendor_prefix == "ollama":
        return _generate_with_ollama(actual_model, contents, schema, temperature, system_prompt, include_thoughts, file, show_params, max_length, check_repetition)
    else:
        raise ValueError(f"Unsupported vendor prefix: {vendor_prefix}")


def _generate_with_gemini(
    model: str,
    contents: List[str],
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
    from . import config_from_schema, generate_content_retry, config_text
    
    # Build config from schema or use text config
    if schema is not None:
        generate_content_config = config_from_schema(schema)
    else:
        generate_content_config = config_text
    
    if temperature is not None:
        generate_content_config.temperature = temperature
    if system_prompt:
        generate_content_config.system_instruction = [system_prompt]
    
    # Generate content
    result = generate_content_retry(
        model=model,
        config=generate_content_config,
        contents=contents,
        show_params=show_params,
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
    contents: List[str],
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

    # Extract base_url from model if present (format: model@base_url)
    base_url = None
    if model and "@" in model:
        model, base_url = model.rsplit("@", 1)

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
        **kwargs
    )


def _generate_with_ollama(
    model: str,
    contents: List[str],
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
