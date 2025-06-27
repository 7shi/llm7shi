import json
import sys
import inspect
from typing import Dict, Any, List, Union, Type
from pydantic import BaseModel

from .utils import contents_to_openai_messages, add_additional_properties_false, do_show_params, inline_defs
from .response import Response


def generate_with_schema(
    contents: List[str],
    schema: Union[Dict[str, Any], Type[BaseModel], None] = None,
    *,
    model: str = None,
    temperature: float = None,
    system_prompt: str = None,
    include_thoughts: bool = True,
    thinking_budget=None,
    file=sys.stdout,
    show_params: bool = True,
    max_length=None,
) -> Response:
    """Generate content using either OpenAI or Gemini API.
    
    Args:
        contents: List of user content strings
        schema: JSON schema for structured output, Pydantic model, or None for plain text
        model: Model name (e.g., "gpt-4.1-mini", "gemini-2.5-flash"). Defaults to Gemini.
        temperature: Temperature parameter for generation (None = use model default)
        system_prompt: System prompt as string
        include_thoughts: Whether to include thinking process (Gemini only)
        thinking_budget: Optional thinking budget (Gemini only)
        file: File to stream output to. Defaults to sys.stdout.
        show_params: Whether to display parameters before generation
        max_length: Maximum length of generated text (default: None, no limit)
        
    Returns:
        Response: Response object containing generated text and metadata
    """
    if model is None or model.startswith("gemini"):
        return _generate_with_gemini(model, contents, schema, temperature, system_prompt, include_thoughts, thinking_budget, file, show_params, max_length)
    else:
        return _generate_with_openai(model, contents, schema, temperature, system_prompt, file, show_params, max_length)


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
        max_length=max_length
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
) -> Response:
    """Generate with OpenAI API with streaming."""
    from openai import OpenAI
    
    # Display parameters if requested
    if show_params and file is not None:
        do_show_params(contents, model=model, file=file)
    
    # Initialize client
    client = OpenAI()
    
    # Convert contents to OpenAI format messages
    openai_messages = contents_to_openai_messages(contents, system_prompt)

    # Build kwargs
    kwargs = {
        "model": model,
        "messages": openai_messages,
        "stream": True
    }
    
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
    
    # Call API with structured output and streaming
    response = client.chat.completions.create(**kwargs)
    
    # Collect streamed response and chunks
    collected_content = ""
    chunks = []
    for chunk in response:
        chunks.append(chunk)
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            collected_content += content
            if file:
                print(content, end='', flush=True, file=file)
            
            # Check max_length and break if exceeded
            if max_length is not None and len(collected_content) >= max_length:
                break
    
    if file and not collected_content.endswith("\n"):
        print(file=file)  # New line after streaming
    
    # Create Response object for OpenAI
    return Response(
        model=model,
        config=kwargs,
        contents=contents,
        response=response,
        chunks=chunks,
        thoughts="",    # OpenAI doesn't have thinking process
        text=collected_content,
    )
