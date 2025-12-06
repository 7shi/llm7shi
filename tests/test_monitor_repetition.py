import pytest
from llm7shi.monitor import detect_repetition


def test_detect_repetition_basic():
    """Test basic repetition detection with new algorithm."""
    # Single character repetition (needs 340 repetitions)
    assert detect_repetition("a" * 340) == True
    assert detect_repetition("a" * 339) == False
    assert detect_repetition("a" * 400) == True

    # Two character repetition (needs 170 repetitions)
    assert detect_repetition("ab" * 170) == True
    assert detect_repetition("ab" * 169) == False

    # Three character repetition (needs 114 repetitions)
    assert detect_repetition("abc" * 114) == True
    assert detect_repetition("abc" * 113) == False

    # Ten character repetition (needs 36 repetitions)
    assert detect_repetition("0123456789" * 36) == True
    assert detect_repetition("0123456789" * 35) == False


def test_detect_repetition_edge_cases():
    """Test edge cases for repetition detection."""
    # Very short text
    assert detect_repetition("a") == False
    assert detect_repetition("ab") == False

    # Pattern at 21 chars (boundary, needs 20 repetitions)
    pattern21 = "abcdefghijklmnopqrstu"  # 21 chars
    assert detect_repetition(pattern21 * 20) == True
    assert detect_repetition(pattern21 * 19 + "different") == False

    # Pattern at 30 chars (needs 20 repetitions)
    pattern30 = "abcdefghijklmnopqrstuvwxyzABCD"  # 30 chars
    assert detect_repetition(pattern30 * 20) == True
    assert detect_repetition(pattern30 * 19 + "different") == False

    # Pattern at 50 chars (needs 20 repetitions)
    pattern50 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX"  # 50 chars
    assert detect_repetition(pattern50 * 20) == True
    assert detect_repetition(pattern50 * 19 + "different") == False

    # Pattern longer than explicit threshold (should not be checked)
    # Create a truly unique 201-char pattern
    base = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    pattern201 = base * 3 + base[:201 - len(base) * 3]  # Exactly 201 chars
    assert len(pattern201) == 201  # Verify length
    assert detect_repetition(pattern201 * 100, threshold=200) == False


def test_detect_repetition_adaptive_threshold():
    """Test adaptive threshold calculation."""
    # Short text: threshold = len(text) // 10
    short_text = "a" * 340  # threshold = 340 // 10 = 34
    assert detect_repetition(short_text) == True  # 340 'a's detected

    # Medium text: adaptive threshold allows longer patterns
    medium_text = "abc" * 114  # 342 chars, threshold = 342 // 10 = 34
    assert detect_repetition(medium_text) == True  # 114 repetitions of "abc"

    # Long text: large adaptive threshold
    long_pattern = "x" * 50  # 50-char pattern
    long_text = long_pattern * 20  # 1000 chars, threshold = 1000 // 10 = 100
    assert detect_repetition(long_text) == True  # 20 repetitions of 50-char pattern

    # Explicit threshold overrides adaptive calculation
    # Create a pattern that only repeats 15 times (not enough for detection)
    base_pattern = "abcdefghij" * 5  # 50 unique chars
    unique_text = base_pattern * 15 + "different_ending"  # Only 15 repetitions (needs 20)
    assert detect_repetition(unique_text, threshold=40) == False  # 50 > 40, not checked


def test_detect_repetition_mixed_content():
    """Test with mixed content."""
    # Normal text followed by repetition
    prefix = "This is normal text. "
    assert detect_repetition(prefix + "x" * 340) == True
    assert detect_repetition(prefix + "xy" * 170) == True

    # Repetition in the middle doesn't count
    assert detect_repetition("a" * 340 + "different text") == False

    # Almost enough repetitions (6 chars needs 58 reps)
    assert detect_repetition("hello " * 57) == False


def test_detect_repetition_custom_threshold():
    """Test with custom threshold values."""
    # Note: Our new formula doesn't use threshold for calculation,
    # but threshold still limits the maximum pattern length to check

    # Small threshold (pattern_len limited to 10)
    assert detect_repetition("a" * 340, threshold=10) == True  # pattern_len=1 needs 340 reps
    assert detect_repetition("ab" * 170, threshold=10) == True   # pattern_len=2 needs 170 reps
    assert detect_repetition("abc" * 114, threshold=10) == True  # pattern_len=3 needs 114 reps

    # Pattern longer than threshold won't be detected
    pattern11 = "abcdefghijk"  # 11 chars
    assert detect_repetition(pattern11 * 100, threshold=10) == False

    # Edge case: threshold=1 (only checks single chars)
    assert detect_repetition("a" * 340, threshold=1) == True
    assert detect_repetition("ab" * 100, threshold=1) == False  # pattern_len=2 > threshold


def test_detect_repetition_formula():
    """Test the new formula: pattern_len < 21 uses dynamic base algorithm, >= 21 uses 20 reps"""
    # Pattern length 1: needs 340 repetitions
    assert detect_repetition("x" * 340) == True
    assert detect_repetition("x" * 339) == False

    # Pattern length 20: needs 21 repetitions (last in lookup table)
    pattern20 = "abcdefghijklmnopqrst"  # Unique 20-char pattern
    assert detect_repetition(pattern20 * 21) == True
    assert detect_repetition(pattern20 * 20 + "different") == False

    # Pattern length 21: needs 20 repetitions (first with fixed value)
    pattern21 = "abcdefghijklmnopqrstu"  # Unique 21-char pattern
    assert detect_repetition(pattern21 * 20) == True
    assert detect_repetition(pattern21 * 19 + "different") == False

    # Pattern length 40: needs 20 repetitions (>= 21)
    pattern40 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"  # Unique 40-char pattern
    assert detect_repetition(pattern40 * 20) == True
    assert detect_repetition(pattern40 * 19 + "different") == False