import pytest
from llm7shi.monitor import detect_repetition


def test_detect_repetition_basic():
    """Test basic repetition detection with new algorithm."""
    # Single character repetition (needs 100 repetitions)
    assert detect_repetition("a" * 100) == True
    assert detect_repetition("a" * 99) == False
    assert detect_repetition("a" * 200) == True
    
    # Two character repetition (needs 54 repetitions)
    assert detect_repetition("ab" * 54) == True
    assert detect_repetition("ab" * 53) == False
    
    # Three character repetition (needs 38 repetitions)
    assert detect_repetition("abc" * 38) == True
    assert detect_repetition("abc" * 37) == False
    
    # Ten character repetition (needs 17 repetitions)
    assert detect_repetition("0123456789" * 17) == True
    assert detect_repetition("0123456789" * 16) == False


def test_detect_repetition_edge_cases():
    """Test edge cases for repetition detection."""
    # Very short text
    assert detect_repetition("a") == False
    assert detect_repetition("ab") == False
    
    # Pattern at 31 chars (boundary, needs 10 repetitions)
    pattern31 = "abcdefghijklmnopqrstuvwxyzABCDE"  # 31 chars
    assert detect_repetition(pattern31 * 10) == True
    assert detect_repetition(pattern31 * 9 + "different") == False
    
    # Pattern at 50 chars (needs 10 repetitions)
    pattern50 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX"  # 50 chars
    assert detect_repetition(pattern50 * 10) == True
    assert detect_repetition(pattern50 * 9 + "different") == False
    
    # Pattern longer than explicit threshold (should not be checked)
    # Create a truly unique 201-char pattern
    base = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    pattern201 = base * 3 + base[:201 - len(base) * 3]  # Exactly 201 chars
    assert len(pattern201) == 201  # Verify length
    assert detect_repetition(pattern201 * 100, threshold=200) == False


def test_detect_repetition_adaptive_threshold():
    """Test adaptive threshold calculation."""
    # Short text: threshold = len(text) // 10
    short_text = "a" * 100  # threshold = 100 // 10 = 10
    assert detect_repetition(short_text) == True  # 100 'a's detected
    
    # Medium text: adaptive threshold allows longer patterns
    medium_text = "abc" * 100  # 300 chars, threshold = 300 // 10 = 30
    assert detect_repetition(medium_text) == True  # 100 repetitions of "abc"
    
    # Long text: large adaptive threshold
    long_pattern = "x" * 50  # 50-char pattern
    long_text = long_pattern * 20  # 1000 chars, threshold = 1000 // 10 = 100
    assert detect_repetition(long_text) == True  # 20 repetitions of 50-char pattern
    
    # Explicit threshold overrides adaptive calculation
    # Create a pattern that only repeats 5 times (not enough for detection)
    base_pattern = "abcdefghij" * 5  # 50 unique chars
    unique_text = base_pattern * 5 + "different_ending"  # Only 5 repetitions
    assert detect_repetition(unique_text, threshold=40) == False  # 50 > 40, not checked


def test_detect_repetition_mixed_content():
    """Test with mixed content."""
    # Normal text followed by repetition
    prefix = "This is normal text. "
    assert detect_repetition(prefix + "x" * 100) == True
    assert detect_repetition(prefix + "xy" * 54) == True
    
    # Repetition in the middle doesn't count
    assert detect_repetition("a" * 100 + "different text") == False
    
    # Almost enough repetitions
    assert detect_repetition("hello " * 11) == False  # 6 chars, needs 12 reps


def test_detect_repetition_custom_threshold():
    """Test with custom threshold values."""
    # Note: Our new formula doesn't use threshold for calculation,
    # but threshold still limits the maximum pattern length to check
    
    # Small threshold (pattern_len limited to 10)
    assert detect_repetition("a" * 100, threshold=10) == True  # pattern_len=1 needs 100 reps
    assert detect_repetition("ab" * 54, threshold=10) == True   # pattern_len=2 needs 54 reps
    assert detect_repetition("abc" * 38, threshold=10) == True  # pattern_len=3 needs 38 reps
    
    # Pattern longer than threshold won't be detected
    pattern11 = "abcdefghijk"  # 11 chars
    assert detect_repetition(pattern11 * 100, threshold=10) == False
    
    # Edge case: threshold=1 (only checks single chars)
    assert detect_repetition("a" * 100, threshold=1) == True
    assert detect_repetition("ab" * 100, threshold=1) == False  # pattern_len=2 > threshold


def test_detect_repetition_formula():
    """Test the new formula: pattern_len < 31 uses linear interpolation, >= 31 uses 10 reps"""
    # Pattern length 1: needs 100 repetitions
    assert detect_repetition("x" * 100) == True
    assert detect_repetition("x" * 99) == False
    
    # Pattern length 20: needs 12 repetitions
    pattern20 = "abcdefghijklmnopqrst"  # Unique 20-char pattern
    assert detect_repetition(pattern20 * 12) == True
    assert detect_repetition(pattern20 * 11 + "different") == False
    
    # Pattern length 30: needs 11 repetitions
    pattern30 = "abcdefghijklmnopqrstuvwxyzABCD"  # Unique 30-char pattern
    assert detect_repetition(pattern30 * 11) == True
    assert detect_repetition(pattern30 * 10 + "different") == False
    
    # Pattern length 40: needs 10 repetitions (>= 31)
    pattern40 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"  # Unique 40-char pattern
    assert detect_repetition(pattern40 * 10) == True
    assert detect_repetition(pattern40 * 9 + "different") == False