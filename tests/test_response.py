"""
Tests for the Response dataclass in response.py.

Usage class tests live in test_usage.py.
"""

from llm7shi.response import Response


class TestResponseUsageDefault:
    def test_defaults_to_none(self):
        assert Response().usage is None
