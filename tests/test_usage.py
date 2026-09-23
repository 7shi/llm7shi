"""
Tests for the Usage class and usage.jsonl persistence helpers in usage.py.

Usage.raw keeps each provider's dict untouched; the properties below are
best-effort normalizations that must correctly fall back across the
different key names and nesting each provider uses (see
docs/20260915-token-usage.md), returning None rather than guessing when a
provider doesn't report a dimension at all.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from llm7shi.usage import (
    Usage,
    append_usage,
    find_usage_file,
    format_usage_line,
    main,
    merge_usage,
    parse_usage_file,
    print_today_totals,
    today,
)


class TestUsageNormalizedFields:
    def test_ollama_shape(self):
        # Ollama reports no total at all, so it must be summed from the two halves
        usage = Usage(raw={
            "prompt_eval_count": 11,
            "eval_count": 385,
            "total_duration": 123,
        })
        assert usage.input_tokens == 11
        assert usage.output_tokens == 385
        assert usage.reasoning_tokens is None
        assert usage.cached_tokens is None
        assert usage.total_tokens == 396

    def test_gemini_shape(self):
        usage = Usage(raw={
            "prompt_token_count": 8,
            "candidates_token_count": 7,
            "thoughts_token_count": 26,
            "total_token_count": 41,
        })
        assert usage.input_tokens == 8
        assert usage.output_tokens == 7
        assert usage.reasoning_tokens == 26
        assert usage.cached_tokens is None
        assert usage.total_tokens == 41  # direct field wins over summing

    def test_openai_responses_shape(self):
        usage = Usage(raw={
            "input_tokens": 13,
            "input_tokens_details": {"cached_tokens": 2, "cache_write_tokens": 0},
            "output_tokens": 13,
            "output_tokens_details": {"reasoning_tokens": 5},
            "total_tokens": 26,
        })
        assert usage.input_tokens == 13
        assert usage.output_tokens == 13
        assert usage.reasoning_tokens == 5
        assert usage.cached_tokens == 2
        assert usage.total_tokens == 26

    def test_openai_chat_completions_shape(self):
        usage = Usage(raw={
            "prompt_tokens": 17,
            "completion_tokens": 147,
            "completion_tokens_details": {"reasoning_tokens": 137},
            "prompt_tokens_details": {"cached_tokens": 0},
            "total_tokens": 164,
        })
        assert usage.input_tokens == 17
        assert usage.output_tokens == 147
        assert usage.reasoning_tokens == 137
        assert usage.cached_tokens == 0
        assert usage.total_tokens == 164

    def test_missing_fields_return_none(self):
        usage = Usage(raw={})
        assert usage.input_tokens is None
        assert usage.output_tokens is None
        assert usage.reasoning_tokens is None
        assert usage.cached_tokens is None
        assert usage.total_tokens is None

    def test_total_tokens_not_computed_without_both_halves(self):
        usage = Usage(raw={"prompt_eval_count": 11})
        assert usage.total_tokens is None


class TestUsageToDict:
    def test_omits_none_fields(self):
        usage = Usage(raw={"prompt_eval_count": 11, "eval_count": 5})
        assert usage.to_dict() == {"input_tokens": 11, "output_tokens": 5, "total_tokens": 16}

    def test_excludes_raw(self):
        usage = Usage(raw={"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3, "extra": "x"})
        d = usage.to_dict()
        assert "raw" not in d
        assert "extra" not in d


class TestUsageRepr:
    def test_matches_to_dict_and_excludes_raw(self):
        usage = Usage(raw={"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3, "extra": "x"})
        assert repr(usage) == f"Usage({usage.to_dict()})"
        assert "extra" not in repr(usage)


class TestUsageAggregation:
    """+ sums the normalized fields, for aggregating usage across multiple calls (e.g. a batch); raw is ignored"""

    def test_add_sums_normalized_fields(self):
        a = Usage(raw={"prompt_eval_count": 10, "eval_count": 20})
        b = Usage(raw={"prompt_eval_count": 5, "eval_count": 7})
        c = a + b
        assert c.to_dict() == {"input_tokens": 15, "output_tokens": 27, "total_tokens": 42}
        # a and b must stay untouched
        assert a.raw == {"prompt_eval_count": 10, "eval_count": 20}
        assert b.raw == {"prompt_eval_count": 5, "eval_count": 7}

    def test_add_ignores_raw(self):
        a = Usage(raw={"prompt_eval_count": 10, "eval_count": 20, "total_duration": 999})
        b = Usage(raw={"prompt_eval_count": 5, "eval_count": 7})
        c = a + b
        assert "total_duration" not in c.raw

    def test_add_treats_missing_field_as_zero_when_either_side_has_it(self):
        a = Usage(raw={"input_tokens": 10, "output_tokens_details": {"reasoning_tokens": 3}})
        b = Usage(raw={"input_tokens": 5})
        c = a + b
        assert c.reasoning_tokens == 3

    def test_add_omits_field_neither_side_has(self):
        a = Usage(raw={"prompt_eval_count": 10, "eval_count": 20})
        b = Usage(raw={"prompt_eval_count": 5, "eval_count": 7})
        c = a + b
        assert c.cached_tokens is None
        assert "cached_tokens" not in c.raw

    def test_add_result_is_chainable(self):
        # a sum's raw uses normalized field names directly, so it must be readable by
        # its own properties too, not just by providers' original field names
        a = Usage(raw={"input_tokens": 10, "output_tokens_details": {"reasoning_tokens": 3}})
        b = Usage(raw={"input_tokens": 5})
        c = Usage(raw={"input_tokens": 2, "output_tokens_details": {"reasoning_tokens": 1}})
        total = (a + b) + c
        assert total.input_tokens == 17
        assert total.reasoning_tokens == 4

    def test_zero_value_default(self):
        assert Usage().raw == {}
        assert Usage().to_dict() == {}

    def test_sum_with_builtin(self):
        usages = [
            Usage(raw={"prompt_eval_count": 10, "eval_count": 20}),
            Usage(raw={"prompt_eval_count": 5, "eval_count": 7}),
        ]
        total = sum(usages)
        assert total.to_dict() == {"input_tokens": 15, "output_tokens": 27, "total_tokens": 42}

    def test_sum_of_empty_list_returns_int_zero(self):
        # sum([]) never calls __radd__; nothing to add to the builtin start value of 0
        assert sum([]) == 0

    def test_radd_rejects_nonzero_int(self):
        assert Usage(raw={"input_tokens": 1}).__radd__(1) is NotImplemented

    def test_iadd_accumulates(self):
        total = Usage()
        total += Usage(raw={"input_tokens": 3, "output_tokens": 2})
        total += Usage(raw={"input_tokens": 5, "output_tokens": 1})
        assert total.to_dict() == {"input_tokens": 8, "output_tokens": 3, "total_tokens": 11}


class TestFormatUsageLine:
    def test_strips_tokens_suffix_and_groups_thousands(self):
        usage = Usage(raw={"prompt_tokens": 746598, "completion_tokens": 1000})
        line = format_usage_line("openai:gpt-5.6-terra", usage)
        assert line == "openai:gpt-5.6-terra|input:746,598|output:1,000|total:747,598"

    def test_omits_fields_the_provider_never_reported(self):
        # Ollama shape: no reasoning/cached breakdown at all
        usage = Usage(raw={"prompt_eval_count": 5, "eval_count": 7})
        assert format_usage_line("ollama:m", usage) == "ollama:m|input:5|output:7|total:12"


class TestAppendAndParseUsageFile:
    def test_append_then_parse_round_trips(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 10, "output_tokens": 20}), "model-a", path, timestamp=ts)

        totals = parse_usage_file(path)
        assert totals == {"2026/09/17": {"model-a": Usage(raw={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30})}}

    def test_multiple_records_same_date_and_model_are_summed(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 10, "output_tokens": 5}), "model-a", path, timestamp=ts)
        append_usage(Usage(raw={"input_tokens": 3, "output_tokens": 2}), "model-a", path, timestamp=ts)

        totals = parse_usage_file(path)
        assert totals["2026/09/17"]["model-a"].to_dict() == {"input_tokens": 13, "output_tokens": 7, "total_tokens": 20}

    def test_date_bucketing_uses_utc(self, tmp_path):
        # 23:30 at UTC-5 is 04:30 the next day in UTC, so the bucket must follow UTC
        path = tmp_path / "usage.jsonl"
        local_ts = datetime(2026, 9, 17, 23, 30, tzinfo=timezone(timedelta(hours=-5)))
        append_usage(Usage(raw={"input_tokens": 1, "output_tokens": 1}), "model-a", path, timestamp=local_ts)

        totals = parse_usage_file(path)
        assert list(totals.keys()) == ["2026/09/18"]

    def test_missing_file_returns_empty_dict(self, tmp_path):
        assert parse_usage_file(tmp_path / "no-such-file.jsonl") == {}


class TestMergeUsage:
    def test_merges_same_day_and_model_into_one_record(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 10, "output_tokens": 5}), "model-a", path, timestamp=ts)
        append_usage(Usage(raw={"input_tokens": 3, "output_tokens": 2}), "model-a", path, timestamp=ts)

        before, after = merge_usage(path)
        assert (before, after) == (2, 1)
        assert parse_usage_file(path)["2026/09/17"]["model-a"].to_dict() == {
            "input_tokens": 13, "output_tokens": 7, "total_tokens": 20,
        }

    def test_merge_is_idempotent(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 10, "output_tokens": 5}), "model-a", path, timestamp=ts)
        merge_usage(path)
        before, after = merge_usage(path)
        assert (before, after) == (1, 1)

    def test_keeps_different_models_separate(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 1}), "model-a", path, timestamp=ts)
        append_usage(Usage(raw={"input_tokens": 2}), "model-b", path, timestamp=ts)

        before, after = merge_usage(path)
        assert (before, after) == (2, 2)


class TestPrintTodayTotals:
    def test_prints_header_and_lines_for_given_date(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 10, "output_tokens": 5}), "model-a", path, timestamp=ts)

        print_today_totals(path, "2026/09/17")
        assert capsys.readouterr().out == "# 2026/09/17\nmodel-a|input:10|output:5|total:15\n"

    def test_does_nothing_when_date_missing(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 1}), "model-a", path, timestamp=ts)

        print_today_totals(path, "2026/09/18")
        assert capsys.readouterr().out == ""

    def test_filters_by_models(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 1}), "model-a", path, timestamp=ts)
        append_usage(Usage(raw={"input_tokens": 2}), "model-b", path, timestamp=ts)
        append_usage(Usage(raw={"input_tokens": 3}), "model-c", path, timestamp=ts)

        print_today_totals(path, "2026/09/17", models=["model-c", "model-a"])
        assert capsys.readouterr().out == "# 2026/09/17\nmodel-a|input:1\nmodel-c|input:3\n"

    def test_accepts_single_model_string(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 1}), "model-a", path, timestamp=ts)
        append_usage(Usage(raw={"input_tokens": 2}), "model-b", path, timestamp=ts)

        print_today_totals(path, "2026/09/17", models="model-b")
        assert capsys.readouterr().out == "# 2026/09/17\nmodel-b|input:2\n"

    def test_does_nothing_when_no_model_matches(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        ts = datetime(2026, 9, 17, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 1}), "model-a", path, timestamp=ts)

        print_today_totals(path, "2026/09/17", models=["model-x"])
        assert capsys.readouterr().out == ""

    def test_defaults_to_find_usage_file_and_today(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        path = find_usage_file()
        append_usage(Usage(raw={"input_tokens": 2, "output_tokens": 3}), "model-a", path)

        print_today_totals()
        assert capsys.readouterr().out == f"# {today()}\nmodel-a|input:2|output:3|total:5\n"


class TestShowCommand:
    def _write(self, path):
        today_ts = datetime.now(timezone.utc)
        old_ts = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
        append_usage(Usage(raw={"input_tokens": 1}), "model-a", path, timestamp=today_ts)
        append_usage(Usage(raw={"input_tokens": 2}), "model-b", path, timestamp=today_ts)
        append_usage(Usage(raw={"input_tokens": 3}), "model-c", path, timestamp=today_ts)
        append_usage(Usage(raw={"input_tokens": 4}), "model-b", path, timestamp=old_ts)

    def test_model_option_repeats(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        self._write(path)

        assert main(["-f", str(path), "show", "-m", "model-a", "--model", "model-c"]) == 0
        assert capsys.readouterr().out == f"# {today()}\nmodel-a|input:1\nmodel-c|input:3\n"

    def test_model_option_with_all_skips_unmatched_dates(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        self._write(path)

        assert main(["-f", str(path), "show", "-a", "-m", "model-c"]) == 0
        assert capsys.readouterr().out == (
            f"# {today()}\nmodel-c|input:3\n\n===== Total =====\nmodel-c|input:3\n"
        )

    def test_model_option_no_match(self, tmp_path, capsys):
        path = tmp_path / "usage.jsonl"
        self._write(path)

        assert main(["-f", str(path), "show", "-m", "model-x"]) == 1
        assert capsys.readouterr().out == "No records for model-x\n"


class TestFindUsageFile:
    def test_uses_xdg_state_home_when_set(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        assert find_usage_file() == tmp_path / "llm7shi" / "usage.jsonl"

    def test_falls_back_to_dot_local_state(self, tmp_path, monkeypatch):
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert find_usage_file() == tmp_path / ".local" / "state" / "llm7shi" / "usage.jsonl"

    def test_creates_parent_directory_but_not_the_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        path = find_usage_file()
        assert path.parent.is_dir()
        assert not path.exists()

    def test_search_upward_finds_file_in_current_directory(self, tmp_path, monkeypatch):
        (tmp_path / "usage.jsonl").write_text("")
        monkeypatch.chdir(tmp_path)
        assert find_usage_file(search_upward=True) == tmp_path / "usage.jsonl"

    def test_search_upward_finds_file_in_ancestor_directory(self, tmp_path, monkeypatch):
        (tmp_path / "usage.jsonl").write_text("")
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)
        assert find_usage_file(search_upward=True) == tmp_path / "usage.jsonl"

    def test_search_upward_raises_when_not_found(self, tmp_path, monkeypatch):
        # an isolated tmp_path has no usage.jsonl anywhere above it
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            find_usage_file(search_upward=True)
