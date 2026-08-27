"""
Tests for the OpenAI API wrapper.

handle_error() must extract the Retry-After hint so 429 responses from
providers like OpenRouter back off for the server-requested duration
instead of the default fixed delay.
"""

import httpx
import openai
import pytest

from llm7shi.openai import OpenAIStreamGenerator


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
