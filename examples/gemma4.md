# gemma4.py - Same Model Across Multiple Providers

## Why This Example Exists

This example demonstrates that a single model can be accessed uniformly across multiple providers. It runs the same Gemma model (`gemma-4-31b-it`) through Google, OpenRouter, and Ollama, pairing each with both `include_thoughts` values to show that the unified interface holds regardless of where the model is hosted.

For the raw, unwrapped API code behind each provider — what llm7shi replaces — see [docs/20260608-provider-apis.md](../docs/20260608-provider-apis.md).

### Why the Same Model on Different Providers
**Problem**: The same open model is often available through several providers at once - a cloud API, an aggregator, and a local runtime. Each exposes the model under a different name and through a different API, so switching providers normally means rewriting code.

**Solution**: Lists the identical model under three vendor prefixes (`google:`, `openrouter:`, `ollama:`) and calls `generate_with_schema()` with no other changes. This makes provider choice a matter of cost, latency, privacy, or availability rather than code, while keeping behavior consistent.

### Consistent Reasoning Control
**Problem**: Even for the same model, providers differ in how reasoning is requested and returned, making the thinking process behave inconsistently when you switch backends.

**Solution**: Toggles `include_thoughts` between `True` and `False` for every provider so you can confirm that the control behaves the same everywhere. llm7shi absorbs the provider-specific details, so `include_thoughts=True` surfaces the reasoning process and `include_thoughts=False` skips it across all three.

### A Provider-Specific Caveat (Google)
**Problem**: The `google:` provider cannot suppress reasoning for Gemma with `include_thoughts=False`. The model keeps generating thought parts server-side regardless of the flag. llm7shi discards these parts so they no longer leak into the answer, but the model still performs the reasoning - you cannot actually turn it off. OpenRouter and Ollama, by contrast, cleanly suppress the reasoning when `include_thoughts=False`.

**Solution**: This is a server-side behavior of the Google API and cannot be worked around on the client. The example surfaces the difference openly so you know what to expect: when you need to genuinely skip reasoning for this model, prefer the OpenRouter or Ollama backends over `google:`.
