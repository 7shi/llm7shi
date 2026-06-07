# gemma4.py - Same Model Across Multiple Providers

## Why This Example Exists

This example demonstrates that a single model can be accessed uniformly across multiple providers. It runs the same Gemma model (`gemma-4-31b-it`) through Google, OpenRouter, and Ollama, pairing each with both `include_thoughts` values to show that the unified interface holds regardless of where the model is hosted.

### Why the Same Model on Different Providers
**Problem**: The same open model is often available through several providers at once - a cloud API, an aggregator, and a local runtime. Each exposes the model under a different name and through a different API, so switching providers normally means rewriting code.

**Solution**: Lists the identical model under three vendor prefixes (`google:`, `openrouter:`, `ollama:`) and calls `generate_with_schema()` with no other changes. This makes provider choice a matter of cost, latency, privacy, or availability rather than code, while keeping behavior consistent.

### Consistent Reasoning Control
**Problem**: Even for the same model, providers differ in how reasoning is requested and returned, making the thinking process behave inconsistently when you switch backends.

**Solution**: Toggles `include_thoughts` between `True` and `False` for every provider so you can confirm that the control behaves the same everywhere. llm7shi absorbs the provider-specific details, so `include_thoughts=True` surfaces the reasoning process and `include_thoughts=False` skips it across all three.

### A Provider-Specific Caveat (Google)
**Problem**: The `google:` provider behaves differently with `include_thoughts=False`. Instead of disabling reasoning, the model still reasons but the thinking process is no longer separated out - it leaks into the answer body, mixing the internal deliberation with the final response. OpenRouter and Ollama, by contrast, cleanly suppress the reasoning when `include_thoughts=False`.

**Solution**: This is a server-side behavior of the Google API and cannot be worked around on the client. The example surfaces the difference openly so you know what to expect: when you need a clean, reasoning-free answer from this model, prefer the OpenRouter or Ollama backends over `google:`.
