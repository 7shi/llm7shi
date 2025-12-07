# Quasi-Repetition Detection Algorithm

This document describes the gap-tolerant quasi-repetition detection algorithm implemented on 2025-12-07.

## Background

### Problem Statement

The original `detect_repetition` function only detected exact repetitions like "foofoofoo...". However, LLMs sometimes produce patterns with small variations:

```
foo1foo2foo3...foo100...
```

Where the numeric counter changes (and may even change in length: 9 → 10 → 100). Traditional exact-match detection misses these patterns because each segment is technically different.

### Design Requirements

1. **Generalized detection**: Handle any type of gap content (numbers, letters, punctuation)
2. **Variable-length gaps**: Support gaps that change in length (e.g., "9", "10", "100")
3. **No normalization**: Avoid text transformation to keep implementation simple
4. **Maintain performance**: O(n) complexity, suitable for real-time streaming
5. **Backward compatibility**: Existing exact-match detection should still work

## Algorithm Design

### Core Concept: Gap-Tolerant Matching

The key insight is that quasi-repetition can be defined by the relationship between pattern length and gap length:

**Gap Constraint**: A pattern P repeats with valid gaps if each gap G between consecutive occurrences satisfies:
```
len(G) < len(P)
```

### Example Analysis

```
"foo1foo2foo100foo"
   ^   ^   ^^^
  gap gap  gap

Pattern: "foo" (3 chars)
Gaps: "1" (1 char), "2" (1 char), "100" (3 chars)

Check: 1 < 3 ✓, 1 < 3 ✓, 3 < 3 ✗

The last gap (3 chars) is NOT less than pattern length (3 chars),
so this would NOT be detected as quasi-repetition.
```

```
"foo1foo2foo99foo"
   ^   ^   ^^
  gap gap gap

Pattern: "foo" (3 chars)
Gaps: "1" (1 char), "2" (1 char), "99" (2 chars)

Check: 1 < 3 ✓, 1 < 3 ✓, 2 < 3 ✓

All gaps are shorter than pattern → quasi-repetition detected.
```

### Algorithm: Backward Gap-Tolerant Scanning

```python
def _check_quasi_repetition(text: str, pattern: str, required_reps: int) -> bool:
    pattern_len = len(pattern)
    text_len = len(text)

    # Must end with pattern
    if not text.endswith(pattern):
        return False

    # Quick check: exact repetition (fastest path)
    if text.endswith(pattern * required_reps):
        return True

    # Scan backward for quasi-repetition
    reps = 1
    pos = text_len - pattern_len

    while reps < required_reps and pos > 0:
        # Search for previous pattern occurrence
        # Gap must be < pattern_len
        found = False
        max_gap = pattern_len - 1

        for gap in range(max_gap + 1):
            prev_start = pos - gap - pattern_len
            if prev_start < 0:
                break

            if text[prev_start:prev_start + pattern_len] == pattern:
                reps += 1
                pos = prev_start
                found = True
                break

        if not found:
            break

    return reps >= required_reps
```

### How It Works

1. **End check**: Pattern must appear at the very end of text
2. **Fast path**: Try exact repetition first (existing optimized algorithm)
3. **Backward scan**: Starting from end, find previous pattern occurrence within gap constraint
4. **Gap search**: For each position, try gap lengths 0, 1, 2, ..., (pattern_len - 1)
5. **Count repetitions**: Continue until required count reached or no valid pattern found

### Integration with Existing Algorithm

The quasi-repetition check is integrated into `detect_repetition()`:

```python
def detect_repetition(text: str, threshold: Optional[int] = None) -> bool:
    # Phase 1: Short patterns (1-10 chars)
    for pattern_len in range(1, min(11, threshold + 1)):
        required_reps = _calculate_required_reps(pattern_len)
        pattern = text[-pattern_len:]

        # Check for exact OR quasi-repetition
        if _check_quasi_repetition(text, pattern, required_reps):
            return True

    # Phase 2: Long patterns (11+ chars) using suffix marker
    # ... similar integration ...
```

## Complexity Analysis

### Time Complexity

**Per pattern length check:**
- Exact match check: O(pattern_len × required_reps)
- Quasi-repetition scan: O(pattern_len × required_reps)
  - For each pattern occurrence: try up to `pattern_len` gap lengths
  - String comparison: O(pattern_len)

**Overall:**
- Phase 1 (patterns 1-10): O(10 × pattern_len × required_reps)
- Phase 2 (patterns 11+): O(k × pattern_len × required_reps) where k = suffix marker occurrences

**Worst case**: O(n) where n = text length

### Space Complexity

- O(1) additional space (no string copies or allocations)

## Edge Cases

### Gap Exactly Equal to Pattern Length

```
"ab" + "XYab" * N  →  gap "XY" (2) is NOT < pattern "ab" (2)
                      NOT detected as "ab" quasi-repetition
```

However, this may still be detected as a different pattern:
- Pattern "Yab" (3 chars) with gap "X" (1 char) → 1 < 3 ✓

### Empty Gaps (Exact Repetition)

```
"abcabcabc"  →  gap = 0, which is < pattern_len (3)
                Detected (fast path handles this)
```

### Variable-Length Gaps

```
"item9item10item11item100item"
    ^    ^^    ^^    ^^^
   1ch   2ch   2ch   3ch

Pattern "item" (4 chars)
All gaps (1, 2, 2, 3) < 4 → detected
```

### Pattern Not at End

```
"foo1foo2foo3X"  →  Does not end with "foo"
                    NOT detected
```

## Threshold Interaction

The existing required repetitions table remains unchanged:

| Pattern Length | Required Reps | Total Length |
|----------------|---------------|--------------|
| 1              | 340           | 340          |
| 2              | 170           | 340          |
| 3              | 114           | 342          |
| 5              | 69            | 345          |
| 10             | 36            | 360          |
| 21+            | 20            | varies       |

Quasi-repetition counts only pattern occurrences (gaps are not counted toward repetition requirements).

## Design Decisions

### Why `gap < pattern` Instead of `gap <= pattern`?

The strict inequality ensures that:
1. The pattern is always the "dominant" element in the sequence
2. More characters come from patterns than from gaps
3. Reduces false positives on text with balanced pattern/gap ratios

### Why Backward Scanning?

1. Repetition loops occur at the **end** of generated text
2. Early termination when gap constraint fails
3. Matches existing algorithm's end-focused design

### Why No Text Normalization?

An alternative approach was considered: replace digits with placeholder, then exact match.

```python
# Alternative approach (not used)
"foo1foo2foo3" → "foo#foo#foo#" → detect "foo#" repetition
```

Rejected because:
1. Gap-tolerant approach is more general (handles any gap content)
2. No additional string allocation needed
3. Variable-length numbers handled naturally
4. Simpler mental model (gap constraint vs. normalization rules)

## Test Cases Summary

### Detection Cases

| Input Pattern | Gap | Result | Reason |
|---------------|-----|--------|--------|
| `"foo" + "1foo" * 113` | 1 char | ✓ | 114 reps, 1 < 3 |
| `"hello" + "_hello" * 68` | 1 char | ✓ | 69 reps, 1 < 5 |
| `"item" + "1item2item...100item"` | 1-3 chars | ✓ | All gaps < 4 |
| `"abc" + "XYabc" * 113` | 2 chars | ✓ | 114 reps, 2 < 3 |

### Non-Detection Cases

| Input Pattern | Gap | Result | Reason |
|---------------|-----|--------|--------|
| `"ab" + "XYab" * N` | 2 chars | ✗ | 2 is not < 2 |
| `"foo" + "XXXXfoo" * N` | 4 chars | ✗ | 4 is not < 3 |
| `"foo1foo2foo3"` | 1 char | ✗ | Only 3 reps, need 114 |
| `"foo1foo2fooX"` | - | ✗ | Doesn't end with "foo" |

## Related Documentation

- [Repetition Detection Algorithm](20250629-repetition-detection.md) - Original exact-match algorithm
- [Repetition Detection Threshold Adjustment](20251206-repetition-threshold.md) - Threshold tuning
