"""
Tests for extract_usage() in the Ollama stream generator.

Ollama's ChatResponse has no separate usage sub-object - usage fields sit on
the same chunk as message/model/timing data - so extract_usage() dumps the
whole chunk and excludes the known non-usage keys, instead of hand-picking
usage keys, so a usage field Ollama adds later still shows up without a code
change here (see docs/20260915-token-usage.md).
"""

from unittest.mock import MagicMock

from llm7shi.ollama import OllamaStreamGenerator


def make_chunk(done, **usage_fields):
    chunk = MagicMock(done=done)
    chunk.model_dump.return_value = {
        "model": "qwen3.5:4b",
        "created_at": "2026-09-15T00:00:00Z",
        "done": done,
        "done_reason": "stop" if done else None,
        "message": {"role": "assistant", "content": "hi"},
        "logprobs": None,
        **usage_fields,
    }
    return chunk


class TestExtractUsage:
    def test_returns_none_without_chunks(self):
        gen = OllamaStreamGenerator()
        assert gen.extract_usage([]) is None

    def test_returns_none_when_last_chunk_not_done(self):
        gen = OllamaStreamGenerator()
        chunks = [make_chunk(done=False)]
        assert gen.extract_usage(chunks) is None

    def test_excludes_non_usage_keys_from_final_chunk(self):
        gen = OllamaStreamGenerator()
        chunks = [
            make_chunk(done=False),
            make_chunk(
                done=True,
                prompt_eval_count=11,
                eval_count=385,
                total_duration=123,
                load_duration=45,
                prompt_eval_duration=6,
                eval_duration=78,
            ),
        ]
        assert gen.extract_usage(chunks) == {
            "prompt_eval_count": 11,
            "eval_count": 385,
            "total_duration": 123,
            "load_duration": 45,
            "prompt_eval_duration": 6,
            "eval_duration": 78,
        }
