import pytest
from llm7shi.monitor import _calculate_trailing_whitespace_weight


def test_calculate_trailing_whitespace_weight_basic():
    """Test basic weighted whitespace calculation."""
    # Spaces only (weight 1 each)
    assert _calculate_trailing_whitespace_weight("text   ") == 3
    assert _calculate_trailing_whitespace_weight("text" + " " * 512) == 512

    # Tabs only (weight 4 each)
    assert _calculate_trailing_whitespace_weight("text\t\t\t") == 12  # 3 + 3*3
    assert _calculate_trailing_whitespace_weight("text" + "\t" * 128) == 512  # 128 + 128*3

    # Newlines only (weight 8 each)
    assert _calculate_trailing_whitespace_weight("text\n\n") == 16  # 2 + 2*7
    assert _calculate_trailing_whitespace_weight("text" + "\n" * 64) == 512  # 64 + 64*7


def test_calculate_trailing_whitespace_weight_crlf():
    """Test \r\n handling."""
    # \r\n should count as single newline (weight 8)
    assert _calculate_trailing_whitespace_weight("text\r\n") == 8  # 2 + 1*7 - 1
    assert _calculate_trailing_whitespace_weight("text\r\n\r\n") == 16  # 4 + 2*7 - 2

    # \n\r should count as two separate newlines (weight 16)
    assert _calculate_trailing_whitespace_weight("text\n\r") == 16  # 2 + 1*7 + 1*7

    # Standalone \r (weight 8)
    assert _calculate_trailing_whitespace_weight("text\r") == 8  # 1 + 1*7


def test_calculate_trailing_whitespace_weight_mixed():
    """Test mixed whitespace types."""
    # 2 spaces, 1 newline, 1 tab
    assert _calculate_trailing_whitespace_weight("text  \n\t") == 14  # 4 + 1*7 + 1*3

    # Various combinations
    assert _calculate_trailing_whitespace_weight("text \t\n") == 13  # 3 + 1*7 + 1*3
    assert _calculate_trailing_whitespace_weight("text\t \t ") == 10  # 4 + 2*3


def test_calculate_trailing_whitespace_weight_edge_cases():
    """Test edge cases."""
    # Empty and no whitespace
    assert _calculate_trailing_whitespace_weight("") == 0
    assert _calculate_trailing_whitespace_weight("text") == 0

    # Only whitespace
    assert _calculate_trailing_whitespace_weight("   ") == 3
    assert _calculate_trailing_whitespace_weight("\n\n") == 16
    assert _calculate_trailing_whitespace_weight("\t\t") == 8  # 2 + 2*3


def test_calculate_trailing_whitespace_weight_threshold():
    """Test threshold values (512 weighted units)."""
    # Exactly at threshold
    assert _calculate_trailing_whitespace_weight("text" + " " * 512) == 512
    assert _calculate_trailing_whitespace_weight("text" + "\t" * 128) == 512
    assert _calculate_trailing_whitespace_weight("text" + "\n" * 64) == 512

    # Just below threshold
    assert _calculate_trailing_whitespace_weight("text" + " " * 511) == 511
    assert _calculate_trailing_whitespace_weight("text" + "\t" * 127) == 508  # 127 + 127*3
    assert _calculate_trailing_whitespace_weight("text" + "\n" * 63) == 504  # 63 + 63*7

    # Above threshold
    assert _calculate_trailing_whitespace_weight("text" + " " * 513) == 513
    assert _calculate_trailing_whitespace_weight("text" + "\t" * 129) == 516  # 129 + 129*3
    assert _calculate_trailing_whitespace_weight("text" + "\n" * 65) == 520  # 65 + 65*7


def test_calculate_trailing_whitespace_weight_combinations():
    """Test combinations that reach threshold."""
    # 256 spaces + 32 newlines = 256 + 32*8 = 512
    assert _calculate_trailing_whitespace_weight("text" + " " * 256 + "\n" * 32) == 512

    # 64 tabs + 64 spaces = 64*4 + 64 = 320, not at threshold
    assert _calculate_trailing_whitespace_weight("text" + "\t" * 64 + " " * 64) == 320

    # 32 tabs + 32 newlines = 32*4 + 32*8 = 384, not at threshold
    assert _calculate_trailing_whitespace_weight("text" + "\t" * 32 + "\n" * 32) == 384
