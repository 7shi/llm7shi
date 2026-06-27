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
