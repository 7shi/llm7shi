# Stream Processor Test Module

## Why This Implementation Exists

### Validation of the Shared Thinking/Answer State Machine
**Problem**: The thinking/answer display logic (header emission, content streaming, accumulation, and monitoring) was previously duplicated across the Gemini, OpenAI, and Ollama providers, each with subtle differences. Consolidating it into `StreamProcessor` removes the duplication but concentrates the risk: a single bug now affects every provider.

**Solution**: Created a dedicated test suite that drives `StreamProcessor` directly with synthetic chunks, asserting that headers appear exactly once, that the thinking/answer transition behaves consistently, and that provider-agnostic guarantees hold regardless of how chunks are split.

### Monitoring Integration and Edge Cases
**Problem**: `StreamProcessor` owns two `StreamMonitor` instances (answer and thoughts). Regressions could break early-termination on max length or repetition, or fail silently when no output file is provided.

**Solution**: Tests verify that max-length and repetition detection stop generation and surface through `max_length_exceeded` / `repetition_detected`, that the empty-output case still terminates with a single newline (matching the original providers), and that `file=None` accumulates text without attempting any display.
