import sys
import os
from typing import List, Dict, Any
from openai import OpenAI

from .response import Response
from .monitor import StreamProcessor, GptOssTemplateFilter

DEFAULT_MODEL = "gpt-4.1-mini"


def generate_content(
    messages: List[Dict[str, Any]],
    model: str = "",
    file=sys.stdout,
    max_length=None,
    check_repetition: bool = True,
    base_url: str = None,
    api_key_env: str = None,
    **kwargs
) -> Response:
    """Generate with OpenAI API with streaming and monitoring.

    Args:
        messages: List of messages in OpenAI format
        model: Model name
        file: Output file for streaming
        max_length: Maximum length of generated text
        check_repetition: Whether to check for repetition
        base_url: Custom API endpoint URL
        api_key_env: Environment variable name containing API key.
                     If None and base_url is specified, api_key will be set to ""
                     to prevent leaking OPENAI_API_KEY to untrusted servers.
        **kwargs: Additional arguments for OpenAI API
    """

    # Use default model if not provided
    if not model:
        model = DEFAULT_MODEL

    # Detect if model uses gpt-oss template (needs filtering)
    # Only activate filter for exact match of "llama.cpp/gpt-oss"
    # Skip filter for structured output (response_format specified) as llama.cpp
    # does not emit control tokens in JSON mode
    has_response_format = 'response_format' in kwargs
    needs_gpt_oss_filter = (model == "llama.cpp/gpt-oss") and not has_response_format

    # Determine API key based on api_key_env and base_url
    if api_key_env is not None:
        # Use specified environment variable
        api_key = os.environ.get(api_key_env, "")
        client = OpenAI(base_url=base_url, api_key=api_key)
    elif base_url is not None:
        # base_url specified but api_key_env is None: use empty string for security
        # This prevents leaking OPENAI_API_KEY to untrusted local servers
        client = OpenAI(base_url=base_url, api_key="")
    else:
        # No base_url, no api_key_env: use default OpenAI client
        # (will automatically use OPENAI_API_KEY environment variable)
        client = OpenAI()

    # Call API with streaming
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        **kwargs
    )

    # Collect streamed response and chunks
    chunks = []
    content_filter = GptOssTemplateFilter() if needs_gpt_oss_filter else None
    processor = StreamProcessor(file=file, max_length=max_length, check_repetition=check_repetition)

    # Track previous lengths for incremental display (gpt-oss filter only)
    previous_thoughts_len = 0
    previous_text_len = 0

    for chunk in response:
        chunks.append(chunk)
        delta = chunk.choices[0].delta

        # Handle reasoning content (OpenRouter / reasoning models expose delta.reasoning)
        reasoning = getattr(delta, "reasoning", None)
        if reasoning:
            if not processor.add_thought(reasoning):
                response.close()
                break

        if delta.content is not None:
            content = delta.content

            # Apply filter if present
            if content_filter:
                content_filter.feed(content)

                # Output incremental thoughts (analysis channel)
                if len(content_filter.thoughts) > previous_thoughts_len:
                    new_thoughts = content_filter.thoughts[previous_thoughts_len:]
                    previous_thoughts_len = len(content_filter.thoughts)
                    if not processor.add_thought(new_thoughts):
                        response.close()
                        break

                # Output incremental text (final channel)
                if len(content_filter.text) > previous_text_len:
                    new_text = content_filter.text[previous_text_len:]
                    previous_text_len = len(content_filter.text)
                    if not processor.add_text(new_text):
                        response.close()
                        break
            else:
                # No filter: direct passthrough
                if not processor.add_text(content):
                    response.close()  # Close stream connection
                    break

    # Flush filter if present
    if content_filter:
        content_filter.flush()

        # Output any remaining thoughts
        if len(content_filter.thoughts) > previous_thoughts_len:
            processor.add_thought(content_filter.thoughts[previous_thoughts_len:])

        # Output any remaining text
        if len(content_filter.text) > previous_text_len:
            processor.add_text(content_filter.text[previous_text_len:])

    processor.finalize()

    # Create Response object for OpenAI
    return Response(
        model=model,
        config=kwargs,
        contents=messages,
        response=response,
        chunks=chunks,
        thoughts=processor.thoughts,
        text=processor.text,
        repetition=processor.repetition_detected,
        max_length=processor.max_length_exceeded,
    )
