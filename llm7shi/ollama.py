import sys
import ollama
from typing import List, Dict, Any, Optional

from .response import Response
from .monitor import StreamProcessor
from .stream import StreamGenerator

DEFAULT_MODEL = "qwen3:4b"  # balances thinking capability and resource needs for local deployment


class OllamaStreamGenerator(StreamGenerator):
    """Ollama-specific stream generator."""

    def __init__(self, *args, client=None, messages=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.messages = messages

    def make_stream(self):
        return self.client.chat(
            model=self.model,
            messages=self.messages,
            stream=True,
            **self.config
        )

    def process_chunk(self, chunk, processor) -> bool:
        # Handle thinking content (same 🤔/💡 display convention as gemini.py)
        if getattr(chunk.message, 'thinking', None) is not None:
            if not processor.add_thought(chunk.message.thinking):
                # ollama has no cancellation endpoint; closing the httpx client is the only
                # way to stop the server-side session when breaking out of the stream early
                self.client._client.close()
                return False

        # Handle regular content
        if chunk.message.content:
            if not processor.add_text(chunk.message.content):
                self.client._client.close()
                return False
        return True

    def handle_error(self, e: Exception) -> Optional[dict]:
        # Ollama is local, no retry logic by default (returns None)
        return None


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
        # not all models support thinking (e.g. Gemma3); check capabilities to avoid an API error
        model_info = client.show(model)
        if "thinking" not in model_info.capabilities:
            kwargs["think"] = False  # Workaround: graceful fallback for unsupported models
    
    generator = OllamaStreamGenerator(
        model=model,
        config=kwargs,
        contents=messages,
        file=file,
        max_length=max_length,
        check_repetition=check_repetition,
        client=client,
        messages=messages,
    )
    return generator.generate()
