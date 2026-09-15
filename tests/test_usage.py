"""
Tests for the Usage class in usage.py.

Usage.raw keeps each provider's dict untouched; the properties below are
best-effort normalizations that must correctly fall back across the
different key names and nesting each provider uses (see
docs/20260915-token-usage.md), returning None rather than guessing when a
provider doesn't report a dimension at all.
"""

from llm7shi.usage import Usage


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
