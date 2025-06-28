import pytest
from llm7shi.utils import detect_repetition


def test_detect_repetition_basic():
    """Test basic repetition detection with new algorithm."""
    # Single character repetition (needs 50 - 1//2 = 50 repetitions)
    assert detect_repetition("a" * 50) == True
    assert detect_repetition("a" * 49) == False
    assert detect_repetition("a" * 100) == True
    
    # Two character repetition (needs 50 - 2//2 = 49 repetitions)
    assert detect_repetition("ab" * 49) == True
    assert detect_repetition("ab" * 48) == False
    
    # Three character repetition (needs 50 - 3//2 = 49 repetitions)
    assert detect_repetition("abc" * 49) == True
    assert detect_repetition("abc" * 48) == False
    
    # Ten character repetition (needs 50 - 10//2 = 45 repetitions)
    assert detect_repetition("0123456789" * 45) == True
    assert detect_repetition("0123456789" * 44) == False


def test_detect_repetition_edge_cases():
    """Test edge cases for repetition detection."""
    # Very short text
    assert detect_repetition("a") == False
    assert detect_repetition("ab") == False
    
    # Pattern at max length (50 chars, needs 50 - 50//2 = 25 repetitions)
    # Use a truly unique 50-char pattern
    pattern50 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX"  # 50 chars
    assert detect_repetition(pattern50 * 25) == True
    assert detect_repetition(pattern50 * 24 + "different") == False
    
    # Pattern longer than threshold (should not be checked)
    pattern51 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"  # 51 chars
    assert detect_repetition(pattern51 * 100) == False


def test_detect_repetition_mixed_content():
    """Test with mixed content."""
    # Normal text followed by repetition
    prefix = "This is normal text. "
    assert detect_repetition(prefix + "x" * 50) == True
    assert detect_repetition(prefix + "xy" * 49) == True
    
    # Repetition in the middle doesn't count
    assert detect_repetition("a" * 50 + "different text") == False
    
    # Almost enough repetitions
    assert detect_repetition("hello " * 8) == False  # Only 8 reps, needs 47


def test_detect_repetition_custom_threshold():
    """Test with custom threshold values."""
    # Small threshold
    assert detect_repetition("a" * 10, threshold=10) == True  # 10 - 1//2 = 10
    assert detect_repetition("ab" * 9, threshold=10) == True   # 10 - 2//2 = 9
    
    # Large threshold
    assert detect_repetition("pattern" * 97, threshold=100) == True  # 100 - 7//2 = 97
    
    # Edge case: threshold=1 (always detects single char at end)
    assert detect_repetition("a", threshold=1) == True
    assert detect_repetition("ab", threshold=1) == True  # Last char 'b' repeats 1 time


def test_detect_repetition_formula():
    """Test the formula: required_reps = threshold - pattern_len // 2"""
    # Pattern length 1: 50 - 0 = 50 repetitions
    assert detect_repetition("x" * 50) == True
    assert detect_repetition("x" * 49) == False
    
    # Pattern length 20: 50 - 10 = 40 repetitions
    pattern20 = "abcdefghijklmnopqrst"  # Unique 20-char pattern
    assert detect_repetition(pattern20 * 40) == True
    assert detect_repetition(pattern20 * 39 + "different") == False
    
    # Pattern length 40: 50 - 20 = 30 repetitions  
    pattern40 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"  # Unique 40-char pattern
    assert detect_repetition(pattern40 * 30) == True
    assert detect_repetition(pattern40 * 29 + "different") == False