# Stream Monitor Module

## Why This Implementation Exists

This module was created to eliminate code duplication between Gemini and OpenAI streaming implementations while providing a unified approach to output quality control.

### Duplication in Stream Processing
**Problem**: Both `generate_content_retry` and `_generate_with_openai` contained identical logic for detecting repetition patterns and enforcing max length limits, leading to maintenance challenges and potential inconsistencies.

**Solution**: Extracted common monitoring logic into `StreamMonitor` class that encapsulates all output validation concerns, allowing both providers to share the same quality control implementation.

### Provider-agnostic Design
**Problem**: Different LLM providers have different streaming APIs and response structures, but output quality concerns are universal.

**Solution**: Designed `StreamMonitor` to be completely independent of provider-specific details, accepting only the accumulated text and returning a simple continue/stop decision.

## Detection Strategy (Moved from provider-specific implementations)

### Optimized Frequency Settings
**Problem**: Initial detection frequencies (every 1024 characters) were too slow to catch problems early, wasting tokens and time on problematic generations.

**Solution**: Optimized detection based on improved algorithm efficiency: pattern detection every 512 characters, weighted whitespace detection every 128 characters. The optimized algorithm (see [docs/20250629-repetition-detection.md](../docs/20250629-repetition-detection.md)) is efficient enough to run more frequently without performance impact.

## Repetition Detection Algorithm

### Pattern Recognition Challenge
**Problem**: Large language models occasionally get stuck in repetitive output loops, which wastes tokens and provides poor user experience. This was particularly noticeable during long generations.

**Solution**: Implemented a pattern detection algorithm that checks for repeating sequences at the end of generated text. The algorithm uses a two-phase approach optimized for performance while maintaining accuracy, with adaptive threshold calculation that scales with text length for optimal detection efficiency.

For detailed information about the algorithm, optimization strategy, and implementation details, see [Repetition Detection Algorithm](../docs/20250629-repetition-detection.md).

### Threshold Adjustment for Coordination (Historical)
**Problem**: The original repetition detection threshold (base=100, requiring 100 repetitions for single characters) was too low in production use, triggering false positives on legitimate repetitive content.

For detailed threshold selection rationale and algorithm investigation, see [Repetition Detection Threshold Adjustment](../docs/20251206-repetition-threshold.md).

### Quasi-Repetition Detection
**Problem**: LLMs sometimes produce patterns that are almost identical but have small variations, such as "foo1foo2foo3...foo100..." where the numeric counter changes. Traditional exact-match detection misses these patterns because each "foo1", "foo2", etc. is technically different.

**Solution**: Extended the repetition detection to recognize "quasi-repetition" patterns where a base pattern repeats with gaps shorter than the pattern length. The algorithm uses `str.rfind()` to efficiently scan backward from the end of text, counting pattern occurrences where the gap between consecutive occurrences satisfies `gap_length < pattern_length`.

**Example**: In "foo1foo2foo3...", the pattern "foo" (3 chars) repeats with gaps "1", "2", "3" (1 char each). Since 1 < 3, this is detected as quasi-repetition of "foo".

**Key Design Decisions**:
- **Gap constraint**: `gap_length < pattern_length` (strictly less than)
- **Efficient backward scanning**: Uses `rfind()` for optimized pattern search from end of text
- **Fast path preserved**: Exact repetition is checked first (existing optimized algorithm)
- **No normalization required**: Works directly on original text, supporting any type of gap content
- **Empty pattern handling**: Returns False immediately for empty patterns

This enhancement detects common LLM degeneration patterns like:
- Incrementing counters: "item1item2item3..."
- Sequential markers: "step_a step_b step_c..."
- Variable-length numbers: "data9data10data100..."

For detailed algorithm design and edge case analysis, see [Quasi-Repetition Detection Algorithm](../docs/20251207-quasi-repetition.md).

## Thinking/Answer Stream Processing

### Duplication of the Display State Machine
**Problem**: Beyond repetition and max-length checking, every provider (Gemini, OpenAI, Ollama) re-implemented the same thinking→answer flow by hand: show the `🤔 **Thinking...**` header once, show the `💡 **Answer:**` header once on transition, stream each chunk through the converter, accumulate `thoughts`/`text`, and run two `StreamMonitor` instances. The header strings, newline handling, and check calls drifted apart between providers (for example, the answer header had a leading newline in Ollama/OpenAI but not in Gemini).

**Solution**: Introduced `StreamProcessor`, a higher-level class that owns the `MarkdownStreamConverter` and both `StreamMonitor` instances and exposes a tiny provider-facing API: `add_thought(chunk)`, `add_text(chunk)`, and `finalize()`. Providers no longer touch the converter or monitors directly; each streaming loop collapses to feeding chunks and breaking when a method returns `False`. This keeps `StreamMonitor` a pure, provider-agnostic text checker while concentrating the display/state concerns in one place.

## Template Filter Integration