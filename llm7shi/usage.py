# Usage dataclass for provider-agnostic token-usage info
from dataclasses import dataclass
from typing import Optional


@dataclass
class Usage:
    """Token-usage info from a provider's streaming response.

    Field names and structure vary per provider/API (see
    docs/20260915-token-usage.md for the source survey), so `raw` keeps
    whatever the provider returned, untouched. The properties below are
    best-effort normalizations that generalize across all providers tracked
    there; each returns None where a provider doesn't report that dimension
    at all (e.g. Ollama has no reasoning or cached-token breakdown).

    Attributes:
        raw: The provider's usage dict with its own field names, e.g.
            "prompt_eval_count"/"eval_count" for Ollama vs
            "input_tokens"/"output_tokens" for OpenAI's Responses API
    """
    raw: dict

    def _first(self, *keys: str) -> Optional[int]:
        for key in keys:
            if (value := self.raw.get(key)) is not None:
                return value
        return None

    def _first_nested(self, *paths: tuple) -> Optional[int]:
        for outer, inner in paths:
            outer_value = self.raw.get(outer)
            if isinstance(outer_value, dict) and (value := outer_value.get(inner)) is not None:
                return value
        return None

    @property
    def input_tokens(self) -> Optional[int]:
        return self._first("input_tokens", "prompt_tokens", "prompt_token_count", "prompt_eval_count")

    @property
    def output_tokens(self) -> Optional[int]:
        return self._first("output_tokens", "completion_tokens", "candidates_token_count", "eval_count")

    @property
    def reasoning_tokens(self) -> Optional[int]:
        # "reasoning_tokens" itself covers __add__'s result (see below); Gemini reports
        # this at the top level under its own name, OpenAI (both APIs) nest it under a *_details dict
        direct = self._first("reasoning_tokens", "thoughts_token_count")
        if direct is not None:
            return direct
        return self._first_nested(
            ("output_tokens_details", "reasoning_tokens"),
            ("completion_tokens_details", "reasoning_tokens"),
        )

    @property
    def cached_tokens(self) -> Optional[int]:
        # "cached_tokens" itself covers __add__'s result (see below); only OpenAI (both
        # APIs) otherwise reports this - Gemini and Ollama don't track cache hits at all
        direct = self._first("cached_tokens")
        if direct is not None:
            return direct
        return self._first_nested(
            ("input_tokens_details", "cached_tokens"),
            ("prompt_tokens_details", "cached_tokens"),
        )

    @property
    def total_tokens(self) -> Optional[int]:
        # every provider but Ollama reports a total directly; Ollama's own API never
        # surfaces a combined count either, so it's summed here from the two halves
        direct = self._first("total_tokens", "total_token_count")
        if direct is not None:
            return direct
        if self.input_tokens is not None and self.output_tokens is not None:
            return self.input_tokens + self.output_tokens
        return None

    def to_dict(self) -> dict:
        """The normalized fields (omitting any the provider didn't report), without `raw`."""
        fields = {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "cached_tokens": self.cached_tokens,
            "total_tokens": self.total_tokens,
        }
        return {k: v for k, v in fields.items() if v is not None}

    def __repr__(self) -> str:
        # raw omitted: it's the noisiest part of the object and dataclasses print on-screen
        # a lot (e.g. bare `response.usage` at a REPL); use .raw directly to inspect it
        return f"Usage({self.to_dict()})"

    def __add__(self, other: "Usage") -> "Usage":
        """Sum the normalized fields, for aggregating usage across multiple calls.

        `raw` is ignored (and absent from the result) since its shape is
        provider-specific and summing it field-by-field wouldn't generalize
        the way the normalized fields already do.
        """
        if not isinstance(other, Usage):
            return NotImplemented
        fields = {}
        for key in ("input_tokens", "output_tokens", "reasoning_tokens", "cached_tokens", "total_tokens"):
            a, b = getattr(self, key), getattr(other, key)
            if a is not None or b is not None:
                fields[key] = (a or 0) + (b or 0)
        return Usage(raw=fields)
