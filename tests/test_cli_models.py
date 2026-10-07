"""
Tests for the `llm7shi models` CLI (no network: fetch_openrouter_models is mocked).
"""

from unittest.mock import patch

from llm7shi.cli import main
from llm7shi.cli.models import format_openrouter_models

MODELS = [
    {
        "id": "z/paid", "context_length": 1048576, "pricing": {"prompt": "0.000003", "completion": "0.000015"},
        "architecture": {"input_modalities": ["text", "video", "image"]},
        "top_provider": {"max_completion_tokens": 128000},
        "supported_parameters": ["reasoning", "tools", "structured_outputs", "response_format"],
        "reasoning": {"mandatory": True}, "expiration_date": "2026-12-31",
    },
    {
        "id": "a/model:free", "context_length": 32768, "pricing": {"prompt": "0", "completion": "0"},
        "architecture": {"input_modalities": ["text"]},
        "top_provider": {"max_completion_tokens": None},
        "supported_parameters": ["reasoning", "response_format"],
        "reasoning": {"mandatory": False, "default_enabled": True}, "expiration_date": None,
    },
    {
        "id": "openrouter/auto", "context_length": 2000000, "pricing": {"prompt": "-1", "completion": "-1"},
        "architecture": {"input_modalities": ["text"]}, "top_provider": {},
        "supported_parameters": [], "expiration_date": None,
    },
]


def _rows(text):
    return [line.split() for line in text.splitlines()[1:]]


def test_sorted_and_formatted():
    rows = _rows(format_openrouter_models(MODELS))
    assert [r[0] for r in rows] == ["a/model:free", "openrouter/auto", "z/paid"]
    assert rows[0] == ["a/model:free", "33K", "-", "0", "0", "-", "on", "-", "mode", "-"]
    assert rows[1] == ["openrouter/auto", "2M", "-", "var", "var", "-", "-", "-", "-", "-"]
    assert rows[2] == ["z/paid", "1M", "128K", "3.00", "15.00", "iv", "must", "yes", "schema", "2026-12-31"]


def test_free_filter():
    assert [r[0] for r in _rows(format_openrouter_models(MODELS, free=True))] == ["a/model:free"]


def test_cli_dispatch(capsys):
    with patch("llm7shi.cli.models.fetch_openrouter_models", return_value=MODELS):
        assert main(["models", "openrouter", "--free"]) == 0
    out = capsys.readouterr().out
    assert "a/model:free" in out and "z/paid" not in out
