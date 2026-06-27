# Stream Generator Testing

## Why This Implementation Exists

Testing the unified retry loop and stream consumption logic presented unique challenges because real-world API rate limits and network errors are stochastic and depend on external services. This test suite validates that retry budgets, backoff countdowns, stream termination, and exception propagation function reliably.

### Challenge 1: Emulating Provider API Errors and Stream Failures
**Problem**: Simulating specific HTTP status codes (like 429 and 500) and connection drops during stream iteration would normally require patching complex internal details of third-party SDK clients (Gemini, OpenAI, Ollama).

**Solution**: Created a `MockStreamGenerator` subclassing `StreamGenerator` with a stateful error map keyed by call attempts. This allows deterministic triggering of custom exceptions (like `KeyError` representing 429) at specific points in the execution flow.

### Challenge 2: Verifying Retry Countdowns and Sleep Offsets
**Problem**: Validating that countdown backoff delays (e.g. 2 seconds) sleep for the exact duration would make tests slow and fragile.

**Solution**: Mocked `time.sleep` and verified that the mock was called exactly `delay + 1` times per retry event (representing the 1-second countdown intervals of `wait_retry`), ensuring correct visual countdown progression without actual test delay.
