import json
import sys
import inspect
from typing import Dict, Any, List, Union, Type
from pydantic import BaseModel

from .utils import contents_to_openai_messages, add_additional_properties_false, do_show_params, inline_defs, detect_repetition
from .response import Response
from .terminal import MarkdownStreamConverter


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
    check_repetition: bool = True,
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
        check_repetition: Whether to check for repetitive patterns (default: True)
        
    Returns:
        Response: Response object containing generated text and metadata
    """
    if model is None or model.startswith("gemini"):
        return _generate_with_gemini(model, contents, schema, temperature, system_prompt, include_thoughts, thinking_budget, file, show_params, max_length, check_repetition)
    else:
        return _generate_with_openai(model, contents, schema, temperature, system_prompt, file, show_params, max_length, check_repetition)


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
    repetition_detected = False  # Track if repetition was detected
    max_length_exceeded = None  # Track if max_length was exceeded
    next_check_size = 1024  # Check at 1KB intervals
    converter = MarkdownStreamConverter()  # For terminal formatting
    
    for chunk in response:
        chunks.append(chunk)
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            collected_content += content
            # Stream formatted output to terminal
            if file:
                print(converter.feed(content), end='', flush=True, file=file)
            
            # Check for repetition every 1KB if enabled
            if check_repetition and len(collected_content) >= next_check_size:
                if detect_repetition(collected_content):
                    repetition_detected = True
                    if file:
                        print(converter.feed("\n\n⚠️ **Repetition detected, stopping generation**\n"), file=file)
                    break
                next_check_size += 1024
            
            # Check max_length and break if exceeded
            if max_length is not None and len(collected_content) >= max_length:
                max_length_exceeded = max_length
                if file:
                    print(converter.feed("\n\n⚠️ **Max length reached, stopping generation**\n"), file=file)
                break
    
    # Flush any remaining markdown formatting
    remaining = converter.flush()
    if remaining and file:
        print(remaining, end='', flush=True, file=file)
    
    # Ensure output ends with newline
    if file and not collected_content.endswith("\n"):
        print(flush=True, file=file)
    
    # Create Response object for OpenAI
    return Response(
        model=model,
        config=kwargs,
        contents=contents,
        response=response,
        chunks=chunks,
        thoughts="",    # OpenAI doesn't have thinking process
        text=collected_content,
        repetition=repetition_detected,
        max_length=max_length_exceeded,
    )
