# test_utils_repetition.py - Repetition Detection Tests

This file contains comprehensive tests for the `detect_repetition()` function in `utils.py`, which is designed to identify repetitive patterns in LLM output to prevent infinite loops.

## Test Overview

The test suite validates the repetition detection algorithm across various scenarios to ensure it correctly identifies problematic patterns while avoiding false positives.

## Test Functions

### test_detect_repetition_basic()

Tests fundamental repetition detection with the default threshold (50).

**Test Cases:**
- **Single character repetition**: 50+ repetitions of 'a' should be detected
- **Multi-character patterns**: Tests 2-char and 3-char patterns with required repetitions
- **Longer patterns**: Tests 10-character patterns
- **Non-repetitive text**: Ensures normal text doesn't trigger false positives

**Key Assertions:**
```python
assert detect_repetition("a" * 50) == True   # 50 repetitions detected
assert detect_repetition("a" * 49) == False  # 49 repetitions not enough
assert detect_repetition("ab" * 49) == True  # 2-char pattern needs 49 reps
assert detect_repetition("abc" * 49) == True # 3-char pattern needs 49 reps
```

### test_detect_repetition_edge_cases()

Tests boundary conditions and edge cases.

**Test Cases:**
- **Very short text**: Single characters and short strings
- **Maximum pattern length**: 50-character patterns at the threshold boundary
- **Oversized patterns**: Patterns longer than 50 characters (should not be detected)

**Key Insight:**
The algorithm only checks patterns up to the threshold length (50 chars by default), so patterns longer than this are ignored.

### test_detect_repetition_mixed_content()

Tests realistic scenarios with mixed content.

**Test Cases:**
- **Normal text + repetition**: Prefix followed by repetitive pattern
- **Repetition in middle**: Ensures only end-of-text repetition is detected
- **Insufficient repetitions**: Patterns that don't meet the minimum threshold

**Example:**
```python
prefix = "This is normal text. "
assert detect_repetition(prefix + "x" * 50) == True  # Detected at end
assert detect_repetition("a" * 50 + "different text") == False  # Not at end
```

### test_detect_repetition_custom_threshold()

Tests the function with non-default threshold values.

**Test Cases:**
- **Small thresholds**: threshold=10 for faster detection
- **Large thresholds**: threshold=100 for more stringent detection
- **Edge case**: threshold=1 (minimal viable threshold)

**Algorithm Validation:**
Confirms the formula `required_reps = threshold - pattern_len // 2` works correctly across different threshold values.

### test_detect_repetition_formula()

Explicitly validates the mathematical formula used for determining required repetitions.

**Formula:** `required_reps = threshold - pattern_len // 2`

**Test Cases:**
- **Pattern length 1**: 50 - 0 = 50 repetitions required
- **Pattern length 20**: 50 - 10 = 40 repetitions required  
- **Pattern length 40**: 50 - 20 = 30 repetitions required

**Purpose:**
Ensures the algorithm correctly scales the repetition requirement based on pattern length - shorter patterns need more repetitions, longer patterns need fewer.

## Algorithm Details

### Detection Logic

The `detect_repetition()` function:

1. **Checks pattern lengths 1-50** (or up to threshold)
2. **Calculates required repetitions** using: `threshold - pattern_len // 2`
3. **Extracts pattern from end** of the text
4. **Validates repetition** using `text.endswith(pattern * required_reps)`
5. **Skips insufficient text** when `len(text) < pattern_len * required_reps`

### Why This Approach?

- **End-focused**: Only checks the end of text where repetition loops typically occur
- **Graduated requirements**: Shorter patterns need more repetitions (stricter)
- **Efficiency**: Uses string operations rather than complex pattern matching
- **Configurable**: Threshold parameter allows tuning sensitivity

## Test Data Patterns

### Unique Pattern Generation

Tests use carefully crafted patterns to avoid false matches:
- **50-char unique pattern**: `"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX"`
- **20-char unique pattern**: `"abcdefghijklmnopqrst"`
- **40-char unique pattern**: `"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"`

These patterns ensure tests validate the intended pattern length without triggering matches on shorter sub-patterns.

## Coverage Analysis

### Positive Cases (Should Detect)
- Exact repetition counts at threshold
- Over-repetition (more than required)
- Various pattern lengths (1, 2, 3, 10, 20, 40, 50 chars)
- Mixed content with repetition at end

### Negative Cases (Should Not Detect)
- Under-repetition (fewer than required)
- Non-repetitive text
- Repetition not at end of text
- Patterns longer than threshold
- Text shorter than required total length

### Boundary Conditions
- Exactly threshold length patterns
- Minimum and maximum valid repetition counts
- Edge case thresholds (1, 10, 100)

## Real-World Scenarios

### LLM Output Loops
The tests simulate common LLM failure modes:
- **Single token loops**: `"a" * 50`
- **Word repetition**: `"hello " * 50`
- **Phrase repetition**: `"abc" * 49`
- **Mixed output**: Normal text followed by loops

### False Positive Prevention
Tests ensure normal content doesn't trigger detection:
- Varied vocabulary text
- Technical content with repeated terms
- Code-like patterns
- Structured data formats

## Usage in Production

### Integration Points
The tested function integrates with:
- `generate_content_retry()` in gemini.py (every 1KB)
- `_generate_with_openai()` in compat.py (every 1KB)

### Performance Considerations
- **Lightweight**: String operations only, no regex
- **Scalable**: Linear time complexity
- **Configurable**: Adjustable threshold for different use cases

### Error Prevention
Tests validate the function helps prevent:
- Infinite generation loops
- Excessive API costs from runaway generation
- Poor user experience from repetitive output
- Resource exhaustion from unbounded text generation

## Running the Tests

```bash
# Run all repetition tests
uv run pytest tests/test_utils_repetition.py -v

# Run specific test
uv run pytest tests/test_utils_repetition.py::test_detect_repetition_basic -v

# Run with coverage
uv run pytest tests/test_utils_repetition.py --cov=llm7shi.utils --cov-report=term-missing
```

## Test Dependencies

- **pytest**: Test framework
- **llm7shi.utils**: Module under test
- **No external dependencies**: Tests use only standard library features

The test suite provides comprehensive validation of the repetition detection algorithm, ensuring it works reliably across diverse scenarios while maintaining good performance characteristics.