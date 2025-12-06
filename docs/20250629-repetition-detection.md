# Repetition Detection Algorithm Optimization

This document describes the optimization of the `detect_repetition` function in llm7shi, implemented on 2025-06-29.

> **Note**: The threshold values described in this document reflect the implementation at the time of writing (2025-06-29). These values were later adjusted on 2025-12-06 to coordinate with weighted whitespace detection. For the current threshold values and implementation details, see [20251206-repetition-threshold.md](20251206-repetition-threshold.md).

## Background

Large language models occasionally get stuck in repetitive output loops, generating the same pattern repeatedly. This wastes tokens and provides poor user experience. The `detect_repetition` function identifies these patterns to enable early termination of generation.

## Original Algorithm

The original implementation checked all patterns from length 1 to `threshold` (default 200) sequentially:

```python
for pattern_len in range(1, threshold + 1):
    required_reps = _calculate_required_reps(pattern_len)
    # Check if text ends with pattern repeated required_reps times
```

This resulted in O(threshold × pattern_length) complexity, causing performance issues with large thresholds.

## Optimized Algorithm

The new implementation uses a two-phase approach that leverages mathematical properties of repetition patterns.

### Adaptive Threshold Calculation

The function now supports dynamic threshold calculation when no explicit threshold is provided:

```python
def detect_repetition(text: str, threshold: Optional[int] = None) -> bool:
    # Set default threshold based on text length
    if threshold is None:
        threshold = len(text) // 10
```

This adaptive approach ensures that:
- **Short texts** get proportionally smaller search windows, improving performance
- **Long texts** get larger search windows for comprehensive detection
- **Memory usage** scales appropriately with input size

### Phase 1: Short Patterns (1-10 characters)

For patterns of length 1-10, we use direct sequential checking with early termination:

```python
for pattern_len in range(1, min(10, threshold) + 1):
    required_reps = _calculate_required_reps(pattern_len)
    
    # Early termination when text is too short
    if pattern_len * required_reps > len(text):
        break
    
    pattern = text[-pattern_len:]
    if text.endswith(pattern * required_reps):
        return True
```

**Key optimization**: Since `pattern_len * required_reps` is monotonically increasing for patterns 1-10, we can break early when the text becomes too short.

#### Example: Pattern Length Requirements

| Pattern Length | Required Reps | Total Length |
|----------------|---------------|--------------|
| 1              | 100           | 100          |
| 2              | 54            | 108          |
| 3              | 38            | 114          |
| 4              | 31            | 124          |
| 5              | 26            | 130          |
| 6              | 23            | 138          |
| 7              | 20            | 140          |
| 8              | 18            | 144          |
| 9              | 17            | 153          |
| 10             | 16            | 160          |

### Phase 2: Long Patterns (11+ characters)

For patterns longer than 10 characters, we use an optimized search based on a key insight: **any repetition pattern longer than 10 characters must contain the last 10 characters of the text**.

```python
suffix_marker = text[-10:]  # Last 10 characters as a marker
min_search_pos = max(len(text) - 10 - threshold, 0)

search_end = len(text) - 10
while True:
    pos = text[:search_end].rfind(suffix_marker)
    
    if pos < min_search_pos:
        break
    
    candidate_pattern = text[pos + 10:]
    required_reps = _calculate_required_reps(len(candidate_pattern))
    
    if text.endswith(candidate_pattern * required_reps):
        return True
    
    search_end = pos
```

#### How It Works

1. **Extract suffix marker**: Take the last 10 characters of the text
2. **Search backwards**: Use `rfind` to locate previous occurrences of this marker
3. **Form candidate patterns**: For each occurrence at position `pos`, the candidate pattern is `text[pos + 10:]`
4. **Check repetition**: Test if the text ends with this pattern repeated the required number of times
5. **Respect threshold**: Stop searching beyond `len(text) - threshold - 10`

#### Example: Finding a 25-character Pattern

Given text ending with: `"...the quick brown fox jumps the quick brown fox jumps the quick brown fox jumps"`

1. **Suffix marker**: `"brown fox "` (last 10 chars)
2. **Find occurrences**: 
   - Position 55: Forms pattern `"brown fox jumps the quick "` (25 chars)
   - Position 30: Forms pattern `"brown fox jumps the quick brown fox jumps the quick "` (50 chars)
3. **Check repetitions**: Pattern at position 55 repeats 3 times, meeting the requirement

## Performance Comparison

### Example 1: Short Text (100 characters)
- **Old algorithm**: Checks patterns 1-100
- **New algorithm**: 
  - Adaptive threshold: 100 // 10 = 10
  - Checks patterns 1-10 only (Phase 1 early termination)
- **Improvement**: 90% reduction in iterations

### Example 2: Long Text (1000 characters) with no repetition
- **Old algorithm**: Checks all patterns 1-200
- **New algorithm**: 
  - Adaptive threshold: 1000 // 10 = 100
  - Phase 1: Checks patterns 1-10
  - Phase 2: Typically finds < 5 occurrences of suffix marker
- **Improvement**: ~95% reduction in iterations

### Example 3: Text with 50-character repetition pattern
- **Old algorithm**: Checks patterns 1-50 before finding match
- **New algorithm**: 
  - Adaptive threshold: Varies based on text length
  - Phase 1: Checks patterns 1-10 (no match)
  - Phase 2: Finds match in first occurrence of suffix marker
- **Improvement**: ~80% reduction in iterations

## Complexity Analysis

- **Old algorithm**: O(threshold × pattern_length)
- **New algorithm**: O(10) + O(occurrences × pattern_length)
  - Where `occurrences` is typically much smaller than `threshold`

## Edge Cases Handled

1. **Empty suffix marker**: If all last 10 characters are identical (e.g., "aaaaaaaaaa"), `rfind` still works correctly
2. **Short texts**: Phase 1 handles texts shorter than 160 characters efficiently
3. **Threshold boundary**: `min_search_pos` calculation ensures we never check patterns longer than threshold
4. **No repetition**: Both phases terminate quickly without false positives

## Formula for Required Repetitions

The `_calculate_required_reps` function determines how many times a pattern must repeat to be considered a "stuck loop":

```python
def _calculate_required_reps(pattern_len: int) -> int:
    if pattern_len >= 31:
        return 10
    else:
        total_len = 100 + (pattern_len - 1) * 8
        return total_len // pattern_len
```

This formula ensures:
- Single character repetitions need 100 occurrences
- Longer patterns need proportionally fewer repetitions
- Patterns of 31+ characters need at least 10 repetitions

### Design Rationale

The formula coefficients (100 and 8) were chosen to maintain consistency with whitespace detection thresholds at the time of implementation:

**Coordination with Whitespace Detection:**
- Whitespace detection threshold: 128 characters
- Repetition detection at 5 characters: ~130 total characters (5 × 26 reps)
- Design intent: 5-character repetition patterns align with whitespace detection threshold

This coordination ensures balanced detection sensitivity across different pattern types, preventing either detection mechanism from being significantly more or less sensitive than the other.

**Monotonic Increase Constraint:**

The formula must ensure that `pattern_len × required_reps` increases monotonically with pattern length. This property is critical for the early termination optimization in Phase 1 (lines 52-54 of monitor.py):

```python
if pattern_len * required_reps > len(text):
    break
```

Without monotonic increase, this optimization would incorrectly skip pattern lengths that should be checked, causing false negatives.

**Formula Properties:**
- Linear interpolation: `total_len = 100 + (pattern_len - 1) × 8`
- Results in increasing total length as pattern length grows
- Provides smooth transition from short to long patterns

## Conclusion

This optimization significantly improves performance while maintaining the same detection accuracy. The two-phase approach efficiently handles both short and long repetition patterns, making the function suitable for real-time use during text generation.