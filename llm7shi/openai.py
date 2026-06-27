import sys
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .response import Response
from .monitor import StreamProcessor, GptOssTemplateFilter
from .stream import StreamGenerator

DEFAULT_MODEL = "gpt-4.1-mini"


class OpenAIStreamGenerator(StreamGenerator):
    """OpenAI-specific stream generator."""

    def __init__(self, *args, client=None, messages=None, needs_gpt_oss_filter=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.messages = messages
        self.needs_gpt_oss_filter = needs_gpt_oss_filter
        
        # State variables for chunk processing (reset on each attempt)
        self.content_filter = None
        self.previous_thoughts_len = 0
        self.previous_text_len = 0

    def make_stream(self):
        import openai
        # Reset filter and offsets on retry
        self.content_filter = GptOssTemplateFilter() if self.needs_gpt_oss_filter else None
        self.previous_thoughts_len = 0
        self.previous_text_len = 0
        
        return self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True,
            **self.config
        )

    def process_chunk(self, chunk, processor) -> bool:
        delta = chunk.choices[0].delta

        # Handle reasoning content (OpenRouter / reasoning models expose delta.reasoning)
        reasoning = getattr(delta, "reasoning", None)
        if reasoning:
            if not processor.add_thought(reasoning):
                return False

        if delta.content is not None:
            content = delta.content

            # Apply filter if present
            if self.content_filter:
                self.content_filter.feed(content)

                # Output incremental thoughts (analysis channel)
                if len(self.content_filter.thoughts) > self.previous_thoughts_len:
                    new_thoughts = self.content_filter.thoughts[self.previous_thoughts_len:]
                    self.previous_thoughts_len = len(self.content_filter.thoughts)
                    if not processor.add_thought(new_thoughts):
                        return False

                # Output incremental text (final channel)
                if len(self.content_filter.text) > self.previous_text_len:
                    new_text = self.content_filter.text[self.previous_text_len:]
                    self.previous_text_len = len(self.content_filter.text)
                    if not processor.add_text(new_text):
                        return False
            else:
                # No filter: direct passthrough
                if not processor.add_text(content):
                    return False
        return True

    def finalize_stream(self, processor) -> None:
        if self.content_filter:
            self.content_filter.flush()

            # Output any remaining thoughts
            if len(self.content_filter.thoughts) > self.previous_thoughts_len:
                processor.add_thought(self.content_filter.thoughts[self.previous_thoughts_len:])

            # Output any remaining text
            if len(self.content_filter.text) > self.previous_text_len:
                processor.add_text(self.content_filter.text[self.previous_text_len:])

    def handle_error(self, e: Exception) -> Optional[dict]:
        import openai
        if isinstance(e, openai.APIError) and e.status_code in [429, 500, 502, 503, 504]:
            return {"status_code": e.status_code}
        return None


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
    """Generate with OpenAI API with streaming and monitoring."""

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

    generator = OpenAIStreamGenerator(
        model=model,
        config=kwargs,
        contents=messages,
        file=file,
        max_length=max_length,
        check_repetition=check_repetition,
        client=client,
        messages=messages,
        needs_gpt_oss_filter=needs_gpt_oss_filter,
    )
    return generator.generate()
