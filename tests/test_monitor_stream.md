# Stream Processor Test Module

## Why This Implementation Exists

### Validation of the Shared Thinking/Answer State Machine
**Problem**: The thinking/answer display logic (header emission, content streaming, accumulation, and monitoring) was previously duplicated across the Gemini, OpenAI, and Ollama providers, each with subtle differences. Consolidating it into `StreamProcessor` removes the duplication but concentrates the risk: a single bug now affects every provider.

**Solution**: Created a dedicated test suite that drives `StreamProcessor` directly with synthetic chunks, asserting that headers appear exactly once, that the thinking/answer transition behaves consistently, and that provider-agnostic guarantees hold regardless of how chunks are split.

### Verification of Blank-Line Suppression at Section Boundaries
**Problem**: Providers historically disagreed on the newline before the answer header (some emitted a leading newline, some did not), so the visual gap between thoughts and the answer varied with how many trailing newlines the model produced. The unified design must instead always render exactly one blank line at the boundary.

**Solution**: Parametrized tests feed thoughts with varying trailing newline counts (none through several) and assert the boundary always collapses to exactly one blank line. Additional tests confirm that blank lines *inside* content are preserved and that trailing blank lines are trimmed to a single terminating newline.

### Protection of Verbatim Server Text (KV-Cache Safety)
**Problem**: The blank-line suppression is a display concern only. If it leaked into the accumulated `thoughts`/`text`, the stored conversation would diverge from what the server returned, desyncing the server-side KV cache when the history is resent.

**Solution**: A dedicated test asserts that `processor.thoughts` and `processor.text` equal the raw concatenation of the input chunks, ensuring display formatting never mutates the data handed back to callers.

### Monitoring Integration and Edge Cases
**Problem**: `StreamProcessor` owns two `StreamMonitor` instances (answer and thoughts). Regressions could break early-termination on max length or repetition, or fail silently when no output file is provided.

**Solution**: Tests verify that max-length and repetition detection stop generation and surface through `max_length_exceeded` / `repetition_detected`, that the empty-output case still terminates with a single newline (matching the original providers), and that `file=None` accumulates text without attempting any display.

### Display Assertions Account for Markdown Conversion
**Problem**: The streamed output passes through `MarkdownStreamConverter`, which turns `**bold**` markers into ANSI escape codes. Naive assertions against the raw header strings would not match the rendered output.

**Solution**: A helper strips ANSI sequences before assertions, and tests match the converted header text (`Thinking...`, `Answer:`) rather than the source markdown, documenting the actual on-screen result.
