"""
Tests for `llm7shi chat` in llm7shi/cli/chat.py (no network: generate_with_schema is mocked).
"""

from unittest.mock import patch

import pytest

from llm7shi.cli import main
from llm7shi.cli.chat import format_stats, token_rates
from llm7shi.response import Response
from llm7shi.usage import Usage


def _run(monkeypatch, lines, fake, args=("test:model",)):
    inputs = iter(lines)

    def fake_input(prompt=""):
        try:
            line = next(inputs)
        except StopIteration:
            raise EOFError  # Ctrl+D
        if line is KeyboardInterrupt:
            raise KeyboardInterrupt  # Ctrl+C
        return line

    monkeypatch.setattr("builtins.input", fake_input)
    with patch("llm7shi.client.generate_with_schema", side_effect=fake) as gen:
        assert main(["chat", *args]) == 0
    return gen


def _reply(messages, *, file, **kwargs):
    file.write("Hi")
    return Response(text="Hi", usage=Usage(raw={"input_tokens": 3, "output_tokens": 10}),
                    start_time=100.0, text_start_time=101.0, end_time=103.0)


def test_turn_shows_usage_and_tps(monkeypatch, capsys):
    gen = _run(monkeypatch, ["Hello"], _reply)
    out = capsys.readouterr().out
    assert "input:3 (3.0 tps) | output:10 (5.0 tps) | total:13" in out
    assert gen.call_args.kwargs["show_params"] is False


def test_think_toggle(monkeypatch, capsys):
    gen = _run(monkeypatch, ["/think", "/think off", "Hello", "/think on", "Again"], _reply)
    out = capsys.readouterr().out
    assert "think: on" in out and "think: off" in out
    assert [c.kwargs["include_thoughts"] for c in gen.call_args_list] == [False, True]


def test_clear_history(monkeypatch, capsys):
    gen = _run(monkeypatch, ["first", "/clear", "second"], _reply)
    assert "history cleared" in capsys.readouterr().out
    # the second call sends only its own prompt, not the first turn
    assert gen.call_args_list[1].args[0] == [{"role": "user", "content": "second"}]


def _records(path):
    import json
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


@pytest.mark.parametrize("args,recorded", [
    (("openai:gpt-x",), True),
    (("gpt-x",), True),
    (("test:model",), False),
    (("--save-usage", "test:model"), True),
])
def test_usage_recording(monkeypatch, tmp_path, capsys, args, recorded):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    path = tmp_path / "llm7shi" / "usage.jsonl"
    _run(monkeypatch, ["one", "two"], _reply, args)
    records = _records(path)
    out = capsys.readouterr().out
    if recorded:
        # one record for the whole session, written on exit
        assert [(r["model"], r["input_tokens"]) for r in records] == [(args[-1], 6)]
        assert "usage: recording to" in out
        assert f"{args[-1]}|input:6|output:20|total:26" in out  # today's totals on exit
    else:
        assert records == []
        assert "recording" not in out


def test_usage_recorded_on_interrupt(monkeypatch, tmp_path, capsys):
    # Ctrl+C is not caught, but the finally still records what the session consumed
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    with pytest.raises(KeyboardInterrupt):
        _run(monkeypatch, ["one", KeyboardInterrupt], _reply, ("openai:gpt-x",))
    assert [r["input_tokens"] for r in _records(tmp_path / "llm7shi" / "usage.jsonl")] == [3]


def test_usage_recorded_for_failed_turn(monkeypatch, tmp_path, capsys):
    # an attempt that consumed tokens before the turn failed is still recorded
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))

    def consume_then_fail(messages, **kwargs):
        raise RuntimeError("boom")

    from llm7shi.client import Client
    original = Client.__call__

    def call(self, prompt, schema=None):
        self.usages.append(Usage(raw={"input_tokens": 5}))
        return original(self, prompt, schema)

    monkeypatch.setattr(Client, "__call__", call)
    _run(monkeypatch, ["one"], consume_then_fail, ("openai:gpt-x",))
    assert [r["input_tokens"] for r in _records(tmp_path / "llm7shi" / "usage.jsonl")] == [5]


def test_exit_and_help(monkeypatch, capsys):
    gen = _run(monkeypatch, ["/help", "/exit", "never sent"], _reply)
    assert "/think on|off" in capsys.readouterr().out
    gen.assert_not_called()


def test_error_keeps_session(monkeypatch, capsys):
    calls = []

    def flaky(messages, **kwargs):
        calls.append(messages)
        if len(calls) == 1:
            raise RuntimeError("boom")
        return _reply(messages, **kwargs)

    _run(monkeypatch, ["first", "second"], flaky)
    assert "RuntimeError: boom" in capsys.readouterr().err
    # the failed turn is not in history, so the second call sends only its own prompt
    assert calls[1] == [{"role": "user", "content": "second"}]


def test_format_stats():
    usages = [Usage(raw={"input_tokens": 1000, "output_tokens": 20}), Usage(raw={"input_tokens": 1000, "output_tokens": 30})]
    assert format_stats([], {}) is None
    assert format_stats(usages, {"input_tokens": 2000.0, "output_tokens": 10.0}) == \
        "input:2,000 (2000.0 tps) | output:50 (10.0 tps) | total:2,050"
    assert format_stats(usages, {}) == "input:2,000 | output:50 | total:2,050"


def _resp(raw, thoughts_start=None, text_start=None):
    return Response(usage=Usage(raw=raw), start_time=0.0, thoughts_start_time=thoughts_start,
                    text_start_time=text_start, end_time=10.0)


def test_token_rates_excludes_reasoning():
    # answer tokens (100 - 60) over the answer span (6s -> 10s)
    resp = _resp({"input_tokens": 40, "output_tokens": 100, "reasoning_tokens": 60}, thoughts_start=2.0, text_start=6.0)
    assert token_rates(resp) == {"input_tokens": 20.0, "output_tokens": 10.0}


def test_token_rates_hidden_thinking():
    # thinking not streamed but counted: its time falls before text_start, not in the answer span
    resp = _resp({"input_tokens": 40, "output_tokens": 100, "reasoning_tokens": 60}, text_start=8.0)
    assert token_rates(resp) == {"input_tokens": 5.0, "output_tokens": 20.0}


def test_token_rates_reasoning_outside_completion():
    # Usage folds reasoning back into output when completion < reasoning, so the answer is completion alone
    raw = {"prompt_tokens": 40, "completion_tokens": 40, "total_tokens": 80,
           "completion_tokens_details": {"reasoning_tokens": 60}}
    resp = _resp(raw, thoughts_start=2.0, text_start=6.0)
    assert token_rates(resp) == {"input_tokens": 20.0, "output_tokens": 10.0}


def test_token_rates_without_reasoning_count():
    # no reasoning count (Ollama): all output timed from the first chunk of either kind
    resp = _resp({"prompt_eval_count": 40, "eval_count": 80}, thoughts_start=2.0, text_start=6.0)
    assert token_rates(resp) == {"input_tokens": 20.0, "output_tokens": 10.0}


def test_token_rates_without_timestamps():
    assert token_rates(Response(usage=Usage(raw={"input_tokens": 3}))) == {}
