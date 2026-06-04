import sys
import ollama
from typing import List, Dict, Any

from .response import Response
from .monitor import StreamProcessor

DEFAULT_MODEL = "qwen3:4b"


def generate_content(
    messages: List[Dict[str, Any]],
    model: str = "",
    file=sys.stdout,
    max_length=None,
    check_repetition: bool = True,
    **kwargs
) -> Response:
    """Generate with Ollama API with streaming and monitoring."""
    client = ollama.Client()
    
    # Use default model if not provided
    if not model:
        model = DEFAULT_MODEL
    
    # Extract think parameter from kwargs
    think = kwargs.get("think", False)
    if think:
        # Check if model supports thinking when requested
        model_info = client.show(model)
        if "thinking" not in model_info.capabilities:
            kwargs["think"] = False  # Workaround: graceful fallback for unsupported models
    
    # Call API with streaming
    response = client.chat(
        model=model,
        messages=messages,
        stream=True,
        **kwargs
    )
    
    # Collect streamed response and chunks
    chunks = []
    processor = StreamProcessor(file=file, max_length=max_length, check_repetition=check_repetition)

    for chunk in response:
        chunks.append(chunk)

        # Handle thinking content
        if getattr(chunk.message, 'thinking', None) is not None:
            if not processor.add_thought(chunk.message.thinking):
                client._client.close()
                break

        # Handle regular content
        if chunk.message.content:
            if not processor.add_text(chunk.message.content):
                client._client.close()
                break

    processor.finalize()

    # Create Response object for Ollama
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
