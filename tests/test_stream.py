"""
Tests for StreamGenerator's retry loop and stream consumption.

Real API rate limits/network errors are stochastic and depend on external
services, so this suite validates retry budgets, backoff countdowns, stream
termination, and exception propagation deterministically via a mock
generator instead.
"""

import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
from llm7shi.stream import StreamGenerator, DEFAULT_MAX_ATTEMPTS, DEFAULT_RETRY_DELAY
from llm7shi.response import Response


class MockStreamGenerator(StreamGenerator):
    """A mock implementation of StreamGenerator for testing."""
    # error_map keyed by call attempt triggers exceptions deterministically, avoiding
    # patching internals of the real Gemini/OpenAI/Ollama SDK clients

    def __init__(self, *args, stream_data=None, error_map=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_data = stream_data or []
        self.error_map = error_map or {}
        self.call_count = 0

    def make_stream(self):
        self.call_count += 1
        if self.call_count in self.error_map:
            raise self.error_map[self.call_count]
        return self.stream_data

    def process_chunk(self, chunk, processor) -> bool:
        if chunk == "STOP":
            return False
        processor.add_text(chunk)
        return True

    def handle_error(self, e):
        if isinstance(e, ValueError):
            return {"status_code": 400}
        if isinstance(e, KeyError):
            return {"status_code": 429, "delay": 2}
        return None


def test_stream_generator_success():
    generator = MockStreamGenerator(
        model="mock-model",
        config={"temp": 0.7},
        contents=["test input"],
        stream_data=["hello", " ", "world"],
        file=None,
    )
    
    response = generator.generate()
    
    assert response.text == "hello world"
    assert response.model == "mock-model"
    assert response.config == {"temp": 0.7}
    assert response.contents == ["test input"]
    assert generator.call_count == 1


def test_stream_generator_early_stop():
    generator = MockStreamGenerator(
        stream_data=["hello", "STOP", "world"],
        file=None,
    )
    
    response = generator.generate()
    assert response.text == "hello"
    assert generator.call_count == 1


def test_stream_generator_retry_success():
    # Attempt 1 raises KeyError (retryable, 429), Attempt 2 succeeds
    error_map = {1: KeyError("Rate limit")}
    generator = MockStreamGenerator(
        stream_data=["success"],
        error_map=error_map,
        file=None,
    )
    
    from unittest.mock import call
    # Mocking sleep instead of waiting out real delays keeps this fast and deterministic
    with patch("time.sleep") as mock_sleep:
        response = generator.generate()
        assert response.text == "success"
        assert generator.call_count == 2
        # delay = 2s, so wait_retry calls sleep(1) three times (for 2, 1, 0)
        assert mock_sleep.call_count == 3
        mock_sleep.assert_has_calls([call(1), call(1), call(1)])


def test_stream_generator_non_retryable_error():
    # Attempt 1 raises TypeError (non-retryable)
    error_map = {1: TypeError("Non retryable")}
    generator = MockStreamGenerator(
        stream_data=["success"],
        error_map=error_map,
        file=None,
    )
    
    with pytest.raises(TypeError):
        generator.generate()
    assert generator.call_count == 1


def test_stream_generator_max_retries_exceeded():
    # Raise retryable errors on all attempts
    error_map = {i: KeyError(f"Error {i}") for i in range(1, 6)}
    generator = MockStreamGenerator(
        stream_data=["success"],
        error_map=error_map,
        file=None,
    )
    
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError, match="Max retries exceeded"):
            generator.generate()
        assert generator.call_count == DEFAULT_MAX_ATTEMPTS
        # 4 retries, each delay = 2s (3 sleep calls each) -> 12 sleep calls
        assert mock_sleep.call_count == 12


def test_module_helpers_delegation():
    from llm7shi.terminal import error, wait_retry
    
    # 1. Test when file has wait_retry / error (delegates)
    mock_file = MagicMock()
    error("test-error", file=mock_file)
    mock_file.error.assert_called_once_with("test-error")
    
    wait_retry(5, "wait", file=mock_file)
    mock_file.wait_retry.assert_called_once_with(5, "wait")
    
    # 2. Test fallback when file does not have methods
    from io import StringIO
    fallback_file = StringIO()
    
    error("standard-error", file=fallback_file)
    assert fallback_file.getvalue() == "standard-error\n"
    
    fallback_file = StringIO()
    with patch("time.sleep") as mock_sleep:
        wait_retry(2, "wait", file=fallback_file)
        assert mock_sleep.call_count == 3
        assert fallback_file.getvalue() == "\rwait 2s\rwait 1s\rwait 0s\n"

