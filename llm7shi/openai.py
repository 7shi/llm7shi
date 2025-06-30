import sys
from typing import List, Dict, Any
from openai import OpenAI

from .response import Response
from .terminal import MarkdownStreamConverter
from .monitor import StreamMonitor

# Initialize OpenAI client
client = OpenAI()

DEFAULT_MODEL = "gpt-4o-mini"


def generate_content(
    messages: List[Dict[str, Any]],
    model: str = "",
    file=sys.stdout,
    max_length=None,
    check_repetition: bool = True,
    **kwargs
) -> Response:
    """Generate with OpenAI API with streaming and monitoring."""
    
    # Use default model if not provided
    if not model:
        model = DEFAULT_MODEL
    
    # Call API with streaming
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        **kwargs
    )
    
    # Collect streamed response and chunks
    collected_content = ""
    chunks = []
    converter = MarkdownStreamConverter()  # For terminal formatting
    monitor = StreamMonitor(converter, max_length=max_length, check_repetition=check_repetition)
    
    for chunk in response:
        chunks.append(chunk)
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            collected_content += content
            # Stream formatted output to terminal
            if file:
                print(converter.feed(content), end='', flush=True, file=file)
            
            # Check for repetition and max length
            if not monitor.check(collected_content, file):
                response.close()  # Close stream connection
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
        contents=messages,
        response=response,
        chunks=chunks,
        thoughts="",    # No thoughts captured
        text=collected_content,
        repetition=monitor.repetition_detected,
        max_length=monitor.max_length_exceeded,
    )
