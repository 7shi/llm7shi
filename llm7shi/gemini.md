# gemini.py - Gemini API Client

## Why This Exists

The Gemini API client was built to address several key challenges when working with Google's Gemini models:

1. **Robust API Interaction**: The raw Gemini API can experience rate limits and transient errors. We needed automatic retry logic with exponential backoff to handle these gracefully.

2. **Thinking Process Visualization**: Gemini 2.5 models support a thinking feature that helps understand the model's reasoning process. This needed to be captured and displayed cleanly.

3. **Streaming with Terminal Formatting**: For better user experience, we wanted real-time output with markdown formatting converted to terminal colors. This required coordinated streaming between API chunks and terminal display.

4. **Structured Output Support**: The library needed to support both free-form text and structured JSON output using schemas, with proper validation and error handling.

5. **Quality Control**: Large language models can sometimes generate repetitive output loops. We needed detection mechanisms to identify and stop such patterns automatically.

## Key Design Decisions

### Response Object
Created a comprehensive `Response` dataclass to capture all aspects of generation - not just the final text, but the model used, configuration, raw API response, streaming chunks, and thinking process. This enables debugging and analysis of API interactions.

### Retry Strategy
Implemented specific retry logic for different error types:
- Rate limits (429): Respect the API's retryDelay
- Server errors (500, 502, 503): Fixed 15-second delays
- Other errors: Fail immediately

### Output Length Control
Added `max_length` parameter to prevent runaway generation costs and `check_repetition` to detect when models get stuck in loops. Quality control logic is now handled by the `StreamMonitor` class (see [monitor.md](monitor.md))

### File Upload Handling
Gemini's file API requires uploading first, then referencing in requests. We abstracted this complexity while ensuring proper cleanup with delete functionality.

### Stream Interruption
Streaming responses can be safely interrupted by simply breaking out of the loop consuming the iterator. No explicit `close()` method is required - the underlying HTTP client libraries (httpx/aiohttp) automatically handle resource cleanup when the generator is garbage collected.

### Immutable Module Constants
The `config_text` constant uses Python's `__getattr__` mechanism to return a fresh `GenerateContentConfig` instance on every access. While it appears as a module-level constant, each access creates a new object, preventing unintended mutations from affecting other code. This maintains backward compatibility with existing code that references `config_text` while eliminating the risk of shared mutable state.
