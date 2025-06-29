# Stream Monitor Module

## Why This Implementation Exists

This module was created to eliminate code duplication between Gemini and OpenAI streaming implementations while providing a unified approach to output quality control.

### Duplication in Stream Processing
**Problem**: Both `generate_content_retry` and `_generate_with_openai` contained identical logic for detecting repetition patterns and enforcing max length limits, leading to maintenance challenges and potential inconsistencies.

**Solution**: Extracted common monitoring logic into `StreamMonitor` class that encapsulates all output validation concerns, allowing both providers to share the same quality control implementation.

### Real-time Pattern Detection
**Problem**: LLMs can sometimes generate repetitive patterns or excessive whitespace during streaming, requiring immediate detection and interruption to avoid wasting tokens and time.

**Solution**: Implemented incremental checking that monitors output every 128 characters for whitespace and every 512 characters for repetition patterns, enabling early termination of problematic generations.

### Provider-agnostic Design
**Problem**: Different LLM providers have different streaming APIs and response structures, but output quality concerns are universal.

**Solution**: Designed `StreamMonitor` to be completely independent of provider-specific details, accepting only the accumulated text and returning a simple continue/stop decision.

## Detection Strategy (Moved from provider-specific implementations)

### Optimized Frequency Settings
**Problem**: Initial detection frequencies (every 1024 characters) were too slow to catch problems early, wasting tokens and time on problematic generations.

**Solution**: Optimized detection based on improved algorithm efficiency:
- **Pattern detection**: Every 512 characters using the optimized `detect_repetition` algorithm
- **Whitespace detection**: Every 128 characters for excessive trailing whitespace (≥128 spaces)
- **Rationale**: The optimized algorithm (see [docs/20250629-repetition-detection.md](../docs/20250629-repetition-detection.md)) is efficient enough to run more frequently without performance impact

### Stream Interruption Handling
**Problem**: Different providers have different mechanisms for closing streaming connections when stopping generation early.

**Solution**: `StreamMonitor` returns a simple boolean, letting each provider handle connection cleanup according to their specific requirements:
- **Gemini**: Simply break from the iterator loop (automatic cleanup)
- **OpenAI**: Call `response.close()` to properly release HTTP connections

## Repetition Detection Algorithm

### Pattern Recognition Challenge
**Problem**: Large language models occasionally get stuck in repetitive output loops, which wastes tokens and provides poor user experience. This was particularly noticeable during long generations.

**Solution**: Implemented a pattern detection algorithm that checks for repeating sequences at the end of generated text. The algorithm uses a two-phase approach optimized for performance while maintaining accuracy.

For detailed information about the algorithm, optimization strategy, and implementation details, see [Repetition Detection Algorithm](../docs/20250629-repetition-detection.md).