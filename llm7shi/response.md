# Response Class

## Why This Design

The `Response` class was created to solve several data management challenges that emerged during LLM API interactions:

### Comprehensive Result Container
**Problem**: LLM API calls return various pieces of information beyond just the generated text - thinking processes, streaming chunks, configuration used, etc. Returning just a string loses valuable debugging and analysis data.

**Solution**: Created a dataclass that captures all aspects of the generation process while providing simple access to the most common use case (the generated text).

### Complete Audit Trail
**Problem**: When debugging LLM interactions or analyzing API behavior, you need access to the original inputs, all streaming chunks, and the raw API responses.

**Solution**: Preserved all data from the API interaction in the Response object, enabling post-processing, debugging, and analysis without needing to re-run expensive API calls.

### Stream Timestamps
**Problem**: Measuring speed from outside (wrapping the output file and timing
the first write) mixed in unrelated time: retry countdowns written to the same
file, markdown buffering before display, and thinking that a model does without
streaming it. Token counts alone can't say how fast a model is.

**Solution**: The stream loop records `time.monotonic()` when each attempt's request
is sent and when it ends (`stream.py`), and `StreamProcessor` records the
arrival of the first thinking and first answer chunk (`monitor.py`), since only
it knows which section a chunk belongs to. The start is reset per attempt, so
waits before API-error retries are excluded, and the end is taken after
`finalize_stream()`, which may still flush buffered answer text. Raw points in
time rather than precomputed durations let callers derive whichever span they
need (time to first token, answer-only speed); a monotonic clock keeps those
spans correct even if the system clock is adjusted mid-stream, at the cost of
the values not being wall-clock times.

For `Response.usage`'s design (the provider-agnostic `Usage` class), see `usage.md`.
