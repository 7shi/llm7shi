# LLM Client Module

## Why This Implementation Exists

To handle multi-turn conversational agents with built-in execution safety, we encapsulate LLM history tracking, XML persistence, and application-layer quality retries into a single stateful, callable client.

### Separation of Concerns in Arguments
**Problem**: Passing configuration values (like output streams, limits, and retry counts) to the invocation method (`__call__`) at every turn clutters the signature and introduces duplication for values that stay constant throughout a session.

**Solution**: Configured shared settings (`file`, `max_length`, and `retries`) once in the constructor (`__init__`). Only turn-specific variables (`prompt` and `schema`) are accepted in `__call__`, keeping the invocation extremely simple.

### Stateful System Prompt Management
**Problem**: System prompts are typically defined by the execution flow (caller logic) rather than the LLM client engine wrapper. Initializing it in `__init__` breaks this separation of concerns, while passing it to every call creates history deduplication and tracking issues.

**Solution**: Added a dedicated `set_system_prompt(system_prompt: str)` method. It inserts a system message at the beginning (index 0) of the history list if none exists, or updates it in-place if already present. This ensures that the system prompt is stored within the history state itself, maintaining serialization integrity (`to_xml`/`load_xml`) without cluttering `__init__` or `__call__`.

### Alignment with Low-Level Wrapper Defaults
**Problem**: Having differing default values between `Client` and `generate_with_schema` creates confusion and unpredictable behavior when switching between low-level and stateful interfaces.

**Solution**: Aligned all matching defaults in the `Client` constructor with `generate_with_schema` (including `max_length=None`, `show_params=True`, and `file=sys.stdout`). This ensures that `Client` behaves exactly as a stateful, runaway-guarded wrapper around the core generation logic without introducing arbitrary default discrepancies.

### Scattered Conversation State and Execution Logic
**Problem**: In conversational systems, maintaining the message history list and coordinating the safety wrappers (like runaway-guarding repetition checks) requires boilerplate code that is often duplicated across different callers.

**Solution**: Grouped chat history management, system prompt assembly, and the quality retry loop into the `Client` class, using python's `__call__` syntax for the primary generation entry point. Calling code simply invokes the client object (e.g. `client(prompt)`), which transparently ensures robust execution and history preservation.

### Inflexible, Hardcoded Retry Judgment
**Problem**: The decision of whether a response is "good enough" to stop retrying was inlined directly in the `__call__` loop. Callers with different quality needs (e.g. requiring valid JSON instead of just non-repetitive text) had no way to change this judgment without copying the whole retry loop.

**Solution**: Extracted the judgment into a `should_retry(resp, schema)` method that returns a reason string (or `None` to accept). Subclasses can override it to implement custom quality gates while reusing the constructor, history management, and retry loop unchanged.

### Schema Validity Is a Stronger Signal Than Text Heuristics
**Problem**: When a `schema` is supplied, checks like repetition/max_length/empty-text are redundant proxies for quality — a response that fails to parse or validate against the schema should be rejected regardless of those heuristics, while a response that satisfies the schema is acceptable even if it happens to trip a heuristic (e.g. looking "repetitive" due to structured JSON keys).

**Solution**: When `schema` is provided, `should_retry` skips the plain-text checks entirely and instead validates `resp.text` as JSON against the schema (full validation via `model_validate_json` for Pydantic models, parseability only for plain JSON-schema dicts since no schema-validation library is a project dependency). The parsed result is stored on `resp.data` so callers don't need to re-parse `resp.text` themselves.
