import re
import sys
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .response import Response
from .monitor import StreamProcessor, GptOssTemplateFilter
from .stream import StreamGenerator

DEFAULT_MODEL = "gpt-4.1-mini"  # optional model param, matching gemini.py's default-model pattern

# Set to True to force Chat Completions even against real OpenAI (e.g. if the
# Responses API misbehaves); flipped as a whole-module escape hatch, not per-call.
USE_COMPLETION = False

# Legacy non-reasoning OpenAI models: the Responses API rejects the `reasoning`
# param on these, so `reasoning` is never sent for them regardless of the caller's
# include_thoughts/reasoning_effort. Blacklist (not a reasoning-model whitelist) so
# new model families default to being treated as reasoning-capable.
NON_REASONING_MODEL_RE = re.compile(r"^gpt-[34]", re.IGNORECASE)


def _handle_openai_error(e: Exception) -> Optional[dict]:
    import openai
    if isinstance(e, openai.APIStatusError) and e.status_code in [429, 500, 502, 503, 504]:
        result = {"status_code": e.status_code}
        retry_after = e.response.headers.get("Retry-After")
        if retry_after is None and isinstance(e.body, dict):
            # some providers (e.g. OpenRouter) only surface it inside the JSON body
            retry_after = e.body.get("error", {}).get("metadata", {}).get("headers", {}).get("Retry-After")
        if retry_after is not None:
            try:
                result["delay"] = int(float(retry_after))
            except (TypeError, ValueError):
                pass
        return result
    return None


def _messages_to_responses_input(messages: List[Dict[str, Any]]):
    """Split Chat-Completions-style messages into (instructions, input items) for the Responses API.

    The Responses API takes the system prompt separately as `instructions` and wants
    each remaining turn's content wrapped in typed parts (input_text for user,
    output_text for assistant) rather than a bare string.
    """
    instructions = None
    input_items = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            instructions = content
        elif role == "user":
            input_items.append({"role": "user", "content": [{"type": "input_text", "text": content}]})
        elif role == "assistant":
            input_items.append({"role": "assistant", "content": [{"type": "output_text", "text": content}]})
    return instructions, input_items


def _response_format_to_text_format(response_format: Dict[str, Any]) -> Dict[str, Any]:
    """Translate a Chat Completions `response_format` kwarg into the Responses API's `text` param."""
    json_schema = response_format["json_schema"]
    return {
        "format": {
            "type": "json_schema",
            "name": json_schema["name"],
            "schema": json_schema["schema"],
            "strict": json_schema.get("strict", True),
        }
    }


class OpenAIStreamGenerator(StreamGenerator):
    """OpenAI-specific stream generator."""
    # thoughts/text split mirrors the 🤔/💡 display convention from gemini.py and ollama.py

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

        # some providers put thinking in delta.reasoning instead of delta.content; independent of
        # the gpt-oss filter below (control-token providers never populate this field)
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
        return _handle_openai_error(e)


class OpenAIResponsesStreamGenerator(StreamGenerator):
    """Responses API stream generator, used for real OpenAI (base_url is None) so
    reasoning models' summaries can be captured (Chat Completions never exposes
    them for standard OpenAI)."""

    def __init__(self, *args, client=None, instructions=None, input_items=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.instructions = instructions
        self.input_items = input_items

    def make_stream(self):
        return self.client.responses.create(
            model=self.model,
            instructions=self.instructions,
            input=self.input_items,
            store=False,  # this library is stateless: no need for OpenAI to retain the response server-side
            stream=True,
            **self.config,
        )

    def process_chunk(self, event, processor) -> bool:
        event_type = getattr(event, "type", None)
        if event_type == "response.reasoning_summary_text.delta":
            if not processor.add_thought(event.delta):
                return False
        elif event_type == "response.output_text.delta":
            if not processor.add_text(event.delta):
                return False
        return True

    def handle_error(self, e: Exception) -> Optional[dict]:
        return _handle_openai_error(e)


def generate_content(
    messages: List[Dict[str, Any]],
    model: str = "",
    file=sys.stdout,
    max_length=None,
    check_repetition: bool = True,
    base_url: str = None,  # points at OpenAI-compatible endpoints (llama.cpp, LocalAI, etc.)
    api_key_env: str = None,
    include_thoughts: bool = True,  # Responses API only: whether to request a reasoning summary
    reasoning_effort: str = None,  # Responses API only: "none"/"minimal"/"low"/"medium"/"high"/"xhigh"/"max" (default: "medium")
    **kwargs
) -> Response:
    """Generate with OpenAI API with streaming and monitoring."""

    # Use default model if not provided
    if not model:
        model = DEFAULT_MODEL

    # llama-server ignores the model name and serves one model at a time, so
    # "llama.cpp/gpt-oss" is repurposed as a client-side marker to select this template's
    # filter, not an actual model identifier. Skipped for structured output because
    # llama.cpp doesn't emit control tokens in JSON mode.
    has_response_format = 'response_format' in kwargs
    needs_gpt_oss_filter = (model == "llama.cpp/gpt-oss") and not has_response_format

    # client is created per request (not a global singleton) so base_url can vary per call;
    # connection pooling at the HTTP level keeps this efficient
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

    # Destination decides the transport, not the model: real OpenAI (base_url is
    # None) always goes through the Responses API; OpenAI-compatible endpoints via
    # base_url keep using Chat Completions, since they don't implement Responses.
    if not USE_COMPLETION and base_url is None:
        instructions, input_items = _messages_to_responses_input(messages)

        responses_kwargs = dict(kwargs)
        if "response_format" in responses_kwargs:
            responses_kwargs["text"] = _response_format_to_text_format(responses_kwargs.pop("response_format"))
        if include_thoughts and not NON_REASONING_MODEL_RE.match(model):
            responses_kwargs["reasoning"] = {"effort": reasoning_effort or "medium", "summary": "auto"}

        generator = OpenAIResponsesStreamGenerator(
            model=model,
            config=responses_kwargs,
            contents=messages,
            file=file,
            max_length=max_length,
            check_repetition=check_repetition,
            client=client,
            instructions=instructions,
            input_items=input_items,
        )
        return generator.generate()

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
