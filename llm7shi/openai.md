# OpenAI Module

## Why This Implementation Exists

### Separation of OpenAI-Specific Streaming Logic
**Problem**: The original `compat.py` module contained all OpenAI API handling logic mixed with schema processing, making the code difficult to maintain and reuse independently.

**Solution**: Extracted the core OpenAI streaming and monitoring functionality into a dedicated module that can be used independently or through the compatibility layer.

### Optional OpenAI Support Architecture
**Problem**: The main library focuses on Gemini API, but OpenAI support was embedded in the compatibility module, creating tight coupling and making it difficult to use OpenAI features independently.

**Solution**: Created a standalone OpenAI module that remains optional and is not included in default exports, allowing users to import it explicitly when needed while keeping the core library focused on Gemini.

### Clean Separation of Concerns
**Problem**: Schema handling and API-specific streaming logic were intermingled, making it difficult to modify or test each component independently.

**Solution**: Moved pure OpenAI streaming and monitoring logic to this module, leaving schema processing responsibilities in the compatibility layer where they belong conceptually.

### Pure API Interface Design
**Problem**: Message format conversion and parameter display logic would create unnecessary dependencies and reduce module independence.

**Solution**: Designed the module to accept pre-converted OpenAI messages format directly, establishing a policy where format conversion is the caller's responsibility, making this a pure OpenAI API wrapper.

### Responses API for Reasoning Summaries
**Problem**: Chat Completions never exposes a reasoning/thinking process for standard OpenAI reasoning models (o1/o3/o4/gpt-5 family) — unlike OpenAI-compatible providers that stream it via `delta.reasoning`, real OpenAI has no equivalent field on that endpoint. The Responses API does expose it (as `response.reasoning_summary_text.delta` events).

**Solution**: Added `OpenAIResponsesStreamGenerator` as a second `StreamGenerator` alongside the existing Chat Completions one. Routing is decided by *destination*, not model: whenever `base_url` is unset (real OpenAI, not a compatible server), every call goes through the Responses API, regardless of which model it names — a `gpt-4.1-mini` call gets the same transport as an `o3-mini` one, just without a `reasoning` param. Calls with `base_url` set (llama.cpp, LocalAI, OpenRouter, Groq, ...) keep using Chat Completions unconditionally, since none of those servers implement the Responses API. `USE_COMPLETION` is a module-level escape hatch to force Chat Completions everywhere, for if the Responses API path misbehaves in practice.

The `base_url` parameter alone isn't a reliable destination check, though: `OpenAI()` resolves an unset `base_url` from the `OPENAI_BASE_URL` env var on its own, so a compatible server set only via that env var (no `model@base_url` syntax) would leave the local `base_url` at `None` and get misrouted to the Responses API, which it doesn't implement. `effective_base_url` (`base_url or os.environ.get("OPENAI_BASE_URL")`) is computed once up front and used for both the client-construction branch and the routing check, so the two stay in sync with what the client actually talks to.

Because the Responses API rejects the `reasoning` param outright on legacy models, `NON_REASONING_MODEL_RE` (a `gpt-[34]` blacklist, not a reasoning-model whitelist) suppresses it for those regardless of `include_thoughts`/`reasoning_effort` — deliberately a blacklist so newer model families default to being treated as reasoning-capable without a code change.

### gpt-oss Template Filter Support
**Problem**: Some OpenAI-compatible servers (particularly llama.cpp with gpt-oss template) emit special control tokens (`<|channel|>`, `<|message|>`, etc.) that separate reasoning process from final output, but these tokens would appear in raw output without filtering.

**Solution**: Integrated `GptOssTemplateFilter` from `monitor.py` that activates only for the exact model name `"llama.cpp/gpt-oss"`, parsing control tokens to separate thoughts (analysis channel) from final text (final channel) with real-time incremental display.

**Structured Output Behavior**: The filter is automatically disabled when `response_format` is specified in kwargs (structured output mode). llama.cpp server does not emit control tokens in JSON mode, instead returning direct JSON output only. This optimization avoids unnecessary filter processing. Note that in JSON mode, the separation between reasoning and final answer via control tokens is not available; users who want to capture reasoning should include dedicated fields (e.g., `reasoning`) in their JSON schema.

See [20260918-llama-cpp.md](../docs/20260918-llama-cpp.md) for the `api_key` placeholder, `delta.reasoning_content`, and `OPENAI_BASE_URL` routing fixes found while testing against a real llama.cpp server, and the decision to keep this filter despite llama.cpp now parsing gpt-oss's control tokens natively on recent builds.

### Reasoning Control on the Chat Completions Path

**Problem**: `include_thoughts`/`reasoning_effort` were already threaded down to `generate_content()` for the `llama.cpp:`/`openai:` vendors, but only the Responses API branch (real OpenAI) read them; the Chat Completions branch (llama.cpp, vLLM, and other `base_url`-routed servers) silently dropped both, so a caller had no way to turn off or tune reasoning on those servers from this library.

**Solution**: The Chat Completions branch now forwards `reasoning_effort` as the top-level `reasoning_effort` kwarg (the shape llama.cpp/vLLM accept directly), and translates `include_thoughts=False` into `extra_body.chat_template_kwargs.enable_thinking = False` — the chat-template variable Qwen3-style templates check to render an empty `<think></think>` block instead of running the model's reasoning turn. It merges into any `extra_body`/`chat_template_kwargs` the caller already set rather than replacing it, so this doesn't clobber OpenRouter's separate `reasoning.enabled` mechanism if a future call site combines the two. See [20260918-llama-cpp.md](../docs/20260918-llama-cpp.md) for the full comparison against the Responses API's `reasoning` object.

