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

    # Note: With quasi-repetition detection, long pattern repetitions may be
    # detected as shorter patterns with gaps. The threshold limits the pattern
    # length checked directly, but quasi-repetition can still find shorter
    # patterns within longer repeating sequences.


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

    # Note: With quasi-repetition detection, patterns longer than threshold
    # may still be detected as shorter patterns with gaps.
    # "abcdefghijk" * 100 contains "efghijk" (7 chars) with gap "abcd" (4 chars)
    # Since 4 < 7, it's detected as quasi-repetition
    pattern11 = "abcdefghijk"  # 11 chars
    assert detect_repetition(pattern11 * 100, threshold=10) == True

    # Edge case: threshold=1 (only checks single chars)
    assert detect_repetition("a" * 340, threshold=1) == True
    # "ab" * 100 has pattern "b" (1 char) with gap "a" (1 char)
    # Since 1 is not < 1, not detected
    assert detect_repetition("ab" * 100, threshold=1) == False


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


def test_detect_quasi_repetition_basic():
    """Test quasi-repetition detection with gaps shorter than pattern."""
    # Pattern "foo" (3 chars) with single-char gaps
    # Gap 1 char < pattern 3 chars, should detect
    text = "foo" + "1foo2foo3foo4foo" * 28 + "5foo"  # 114 occurrences
    assert detect_repetition(text) == True

    # Pattern "hello" (5 chars) with single-char gaps
    # Gap 1 char < pattern 5 chars, should detect
    text = "hello" + "_hello" * 68  # 69 occurrences (needs 69 for 5-char pattern)
    assert detect_repetition(text) == True

    # Variable-length gaps (all shorter than pattern)
    # "item" (4 chars) with gaps "1", "2", "10", "100" etc.
    text = "item" + "".join([str(i) + "item" for i in range(1, 86)])  # 86 occurrences
    assert detect_repetition(text) == True


def test_detect_quasi_repetition_gap_boundary():
    """Test gap boundary conditions."""
    # Gap equal to pattern length - no subpattern can have smaller gap
    # Pattern "ab" (2 chars), gap "cd" (2 chars) - forms "abcd" which repeats exactly
    # This will be detected as exact repetition of "abcd"
    text = "abcd" * 200
    assert detect_repetition(text) == True  # Exact repetition of "abcd"

    # Gap one less than pattern length should detect
    # Pattern "abc" (3 chars), gap "XY" (2 chars) - 2 < 3
    text = "abc" + "XYabc" * 113  # 114 occurrences
    assert detect_repetition(text) == True

    # Gap longer than pattern length should NOT detect as that pattern
    # But may be detected as a different pattern if subpatterns exist
    # Use a pattern where no subpattern+gap combo works
    # Pattern "ab" with gap "cdef" (4 chars) - "ab" cannot be detected (4 >= 2)
    # But "fab" (3 chars) with gap "cde" (3 chars) - also no (3 >= 3)
    # And "efab" (4 chars) with gap "cd" (2 chars) - 2 < 4, so detected!
    # Use truly uniform gaps that prevent any subpattern detection
    text = "x" * 340  # 1-char pattern with gap 0, exact repetition
    assert detect_repetition(text) == True

    # Test with gap >= pattern for ALL possible subpatterns
    # "ab" repeated with "cdef" gaps - creates "abcdefabcdef..."
    # This is just exact repetition of "abcdef" (6 chars)
    # 6-char pattern needs 58 reps
    text = "abcdef" * 57  # Only 57 reps, not enough
    assert detect_repetition(text) == False


def test_detect_quasi_repetition_not_enough_reps():
    """Test that quasi-repetition requires enough repetitions."""
    # Pattern "foo" (3 chars) needs 114 reps, but only 10
    text = "foo" + "1foo2foo3foo4foo5foo6foo7foo8foo9foo"  # 11 occurrences
    assert detect_repetition(text) == False

    # Pattern "ab" (2 chars) needs 170 reps, but only 50
    text = "ab" + "_ab" * 49  # 50 occurrences
    assert detect_repetition(text) == False


def test_detect_quasi_repetition_must_end_with_pattern():
    """Test that pattern must appear at the end of text."""
    # Pattern "foo" with gaps, but doesn't end with "foo"
    text = "foo1foo2foo3foo4foo5X"  # Ends with "X", not "foo"
    assert detect_repetition(text) == False

    # Same pattern but ending with pattern
    text = "foo1foo2foo3foo4foo5" + "foo"  # Ends with "foo"
    # Still only 6 occurrences, not enough
    assert detect_repetition(text) == False


def test_detect_quasi_repetition_mixed_exact_and_gaps():
    """Test detection of patterns with mixed exact repetitions and gaps."""
    # Mix of exact repetition and gaps
    # "abc" repeats with some gaps, some without
    # 3-char pattern needs 114 reps
    text = "abc" * 50 + "1abc" * 30 + "abc" * 34  # 114 occurrences total
    assert detect_repetition(text) == True

    # Start with gaps, end with exact
    # Need 114 total: "1abc2abc3abc" = 3 "abc" per unit
    # 38 * 3 = 114, so we need 38 repetitions of the pattern
    text = "1abc2abc3abc" * 38  # 114 occurrences
    assert detect_repetition(text) == True

    # Note: "1abc2abc3abc" * 37 = 111 "abc" occurrences, which is < 114 required
    # However, the 12-char pattern "1abc2abc3abc" itself is detected as exact
    # repetition (12-char pattern needs 28 reps, and 37 > 28)
    # This is expected behavior - quasi-repetition detection is more sensitive