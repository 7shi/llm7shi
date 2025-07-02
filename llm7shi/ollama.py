import sys
from typing import List, Dict, Any
from ollama import chat

from .response import Response
from .terminal import MarkdownStreamConverter
from .monitor import StreamMonitor

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
    
    # Use default model if not provided
    if not model:
        model = DEFAULT_MODEL
    
    # Call API with streaming
    response = chat(
        model=model,
        messages=messages,
        stream=True,
        **kwargs
    )
    
    # Collect streamed response and chunks
    collected_content = ""
    thoughts = ""
    thoughts_shown = False  # Track if thinking header was shown
    answer_shown = False  # Track if answer header was shown
    chunks = []
    converter = MarkdownStreamConverter()  # For terminal formatting
    monitor = StreamMonitor(converter, max_length=max_length, check_repetition=check_repetition)
    
    for chunk in response:
        chunks.append(chunk)
        
        # Handle thinking content
        if hasattr(chunk.message, 'thinking') and chunk.message.thinking is not None:
            thinking_content = chunk.message.thinking
            if not thoughts_shown:
                if file:
                    print(converter.feed("\n🤔 **Thinking...**\n"), file=file)
                thoughts_shown = True
            thoughts += thinking_content
            # Stream formatted thinking output to terminal
            if file:
                print(converter.feed(thinking_content), end='', flush=True, file=file)
        
        # Handle regular content
        if chunk.message.content is not None:
            content = chunk.message.content
            if thoughts_shown and not answer_shown:
                if file:
                    print(converter.feed("💡 **Answer:**\n"), file=file)
                answer_shown = True
            collected_content += content
            # Stream formatted output to terminal
            if file:
                print(converter.feed(content), end='', flush=True, file=file)
            
            # Check for repetition and max length
            if not monitor.check(collected_content, file):
                break
    
    # Flush any remaining markdown formatting
    remaining = converter.flush()
    if remaining and file:
        print(remaining, end='', flush=True, file=file)
    
    # Ensure output ends with newline
    if file and not collected_content.endswith("\n"):
        print(flush=True, file=file)
    
    # Create Response object for Ollama
    return Response(
        model=model,
        config=kwargs,
        contents=messages,
        response=response,
        chunks=chunks,
        thoughts=thoughts,
        text=collected_content,
        repetition=monitor.repetition_detected,
        max_length=monitor.max_length_exceeded,
    )