"""
Tests for the OpenAI API wrapper.

handle_error() must extract the Retry-After hint so 429 responses from
providers like OpenRouter back off for the server-requested duration
instead of the default fixed delay.
"""

import httpx
import openai
import pytest
from unittest.mock import MagicMock, patch

from llm7shi.openai import OpenAIStreamGenerator, OpenAIResponsesStreamGenerator, generate_content


def make_error(status_code=429, headers=None, body=None):
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code, headers=headers or {}, request=request)
    return openai.APIStatusError("boom", response=response, body=body)


class TestHandleError:
    def test_retry_after_header_takes_priority(self):
        gen = OpenAIStreamGenerator()
        e = make_error(
            headers={"Retry-After": "60"},
            body={"error": {"metadata": {"headers": {"Retry-After": "999"}}}},
        )
        assert gen.handle_error(e) == {"status_code": 429, "delay": 60}

    def test_falls_back_to_body_metadata_headers(self):
        gen = OpenAIStreamGenerator()
        e = make_error(
            body={"error": {"metadata": {"headers": {"Retry-After": "60"}}}},
        )
        assert gen.handle_error(e) == {"status_code": 429, "delay": 60}

    def test_no_retry_after_available(self):
        gen = OpenAIStreamGenerator()
        e = make_error(body={"error": {"message": "boom"}})
        assert gen.handle_error(e) == {"status_code": 429}

    def test_non_retryable_status_code(self):
        gen = OpenAIStreamGenerator()
        e = make_error(status_code=400)
        assert gen.handle_error(e) is None

    def test_non_api_status_error_is_not_retryable(self):
        gen = OpenAIStreamGenerator()
        e = openai.APIConnectionError(request=httpx.Request("POST", "https://example.com"))
        assert gen.handle_error(e) is None


class TestOpenAIStreamGeneratorExtractUsage:
    """stream_options={"include_usage": True} (set in make_stream) delivers usage as
    an extra chunk after the one with finish_reason, identifiable by choices=[]"""

    @staticmethod
    def make_usage_chunk(data):
        chunk = MagicMock(choices=[])
        chunk.usage.model_dump.return_value = data
        return chunk

    def test_finds_usage_on_the_extra_chunk(self):
        gen = OpenAIStreamGenerator()
        chunks = [
            MagicMock(choices=[MagicMock()], usage=None),
            self.make_usage_chunk({"prompt_tokens": 5, "completion_tokens": 7}),
        ]
        assert gen.extract_usage(chunks) == {"prompt_tokens": 5, "completion_tokens": 7}

    def test_returns_none_without_a_usage_chunk(self):
        gen = OpenAIStreamGenerator()
        chunks = [MagicMock(choices=[MagicMock()], usage=None)]
        assert gen.extract_usage(chunks) is None

    def test_process_chunk_skips_the_empty_choices_usage_chunk(self):
        gen = OpenAIStreamGenerator()
        processor = MagicMock()
        chunk = MagicMock(choices=[])
        assert gen.process_chunk(chunk, processor) is True
        processor.add_text.assert_not_called()


class TestOpenAIResponsesStreamGeneratorExtractUsage:
    """usage lives on the final response.completed event, inside response.usage"""

    def test_finds_usage_on_the_completed_event(self):
        gen = OpenAIResponsesStreamGenerator()
        completed = MagicMock(type="response.completed")
        completed.response.usage.model_dump.return_value = {"input_tokens": 3, "output_tokens": 4}
        chunks = [MagicMock(type="response.output_text.delta"), completed]
        assert gen.extract_usage(chunks) == {"input_tokens": 3, "output_tokens": 4}

    def test_returns_none_without_a_completed_event(self):
        gen = OpenAIResponsesStreamGenerator()
        chunks = [MagicMock(type="response.output_text.delta")]
        assert gen.extract_usage(chunks) is None


class TestChatCompletionsReasoningControl:
    """Chat Completions path (llama.cpp, vLLM, ...): reasoning_effort/include_thoughts
    must reach client.chat.completions.create() as the top-level reasoning_effort param
    and extra_body.chat_template_kwargs.enable_thinking, respectively, without disturbing
    an extra_body a caller already set (e.g. OpenRouter's reasoning.enabled)."""

    @staticmethod
    def _run(mock_openai_class, **kwargs):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = iter([])
        generate_content(
            messages=[{"role": "user", "content": "Test"}],
            model="qwen3.8",
            file=None,
            base_url="http://localhost:8080/v1",
            **kwargs,
        )
        return mock_client.chat.completions.create.call_args.kwargs

    @patch('llm7shi.openai.OpenAI')
    def test_reasoning_effort_forwarded(self, mock_openai_class):
        call_kwargs = self._run(mock_openai_class, reasoning_effort="low")
        assert call_kwargs["reasoning_effort"] == "low"

    @patch('llm7shi.openai.OpenAI')
    def test_include_thoughts_false_disables_thinking(self, mock_openai_class):
        call_kwargs = self._run(mock_openai_class, include_thoughts=False)
        assert call_kwargs["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False

    @patch('llm7shi.openai.OpenAI')
    def test_include_thoughts_true_omits_extra_body(self, mock_openai_class):
        call_kwargs = self._run(mock_openai_class, include_thoughts=True)
        assert "extra_body" not in call_kwargs

    @patch('llm7shi.openai.OpenAI')
    def test_reasoning_effort_none_omits_param(self, mock_openai_class):
        call_kwargs = self._run(mock_openai_class)
        assert "reasoning_effort" not in call_kwargs

    @patch('llm7shi.openai.OpenAI')
    def test_preserves_existing_extra_body(self, mock_openai_class):
        call_kwargs = self._run(
            mock_openai_class,
            include_thoughts=False,
            extra_body={"reasoning": {"enabled": False}},
        )
        assert call_kwargs["extra_body"]["reasoning"] == {"enabled": False}
        assert call_kwargs["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False
