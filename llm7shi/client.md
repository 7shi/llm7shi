# LLM Client Module

## Why This Implementation Exists

To handle multi-turn conversational agents with built-in execution safety, we encapsulate LLM history tracking, XML persistence, and application-layer quality retries into a single stateful, callable client.

### Alignment with Low-Level Wrapper Defaults
**Problem**: Having differing default values between `Client` and `generate_with_schema` creates confusion and unpredictable behavior when switching between low-level and stateful interfaces.

**Solution**: Aligned all matching defaults in the `Client` constructor with `generate_with_schema` (including `max_length=None`, `show_params=True`, and `file=sys.stdout`). This ensures that `Client` behaves exactly as a stateful, runaway-guarded wrapper around the core generation logic without introducing arbitrary default discrepancies.

### History Accumulation in Batch Callers
**Problem**: `Client` records every turn, which is what a conversation needs but the opposite of what a batch of independent items needs. A caller that reused one client across a long run resent the whole transcript on every item, growing each request quadratically until token usage and rate limits became the symptom. The workaround — a fresh `copy()` per item — had to be repeated at every call site and explained in a comment each time.

**Solution**: Added the `keep_history` constructor flag. It gates only the writing of turns, not the sending of history: with `keep_history=False` a system prompt set once still applies to every call, while independent calls stop accumulating each other's turns. Kept on by default so existing multi-turn code is unaffected, making the batch case a decision made once, where the client is constructed, rather than a discipline enforced at every call.

### Schema Descriptions Not Reaching the Model
**Problem**: A schema's field `description`s are not guidance text for every provider. Ollama's `format=<json schema>` uses the schema only to constrain decoding, so the model never sees the descriptions and an opaque field name stays unexplained. The fix — appending `create_json_descriptions_prompt(schema)` to the prompt — already exists, but every caller had to repeat it at each schema call, which is the same per-call-site discipline `keep_history` was introduced to remove.

**Solution**: Added the `add_json_descriptions` constructor flag. When set, a call that passes `schema` appends the rendered descriptions as a final user message, so it is recorded in history and resent on retries exactly like any other prompt segment. Off by default: it changes the text actually sent, which can shift output even where schema descriptions already work (Gemini/OpenAI). Deliberately kept out of the low-level `generate_with_schema()` path, which stays explicit (see [compat.md](compat.md)) — `Client` is the convenience layer, so conveniences belong here.

### Scattered Conversation State and Execution Logic
**Problem**: In conversational systems, maintaining the message history list and coordinating the safety wrappers (like runaway-guarding repetition checks) requires boilerplate code that is often duplicated across different callers.

**Solution**: Grouped chat history management, system prompt assembly, and the quality retry loop into the `Client` class, using python's `__call__` syntax for the primary generation entry point. Calling code simply invokes the client object (e.g. `client(prompt)`), which transparently ensures robust execution and history preservation.
