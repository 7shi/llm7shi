# openrouter.py - OpenRouter Reasoning Control Example

## Why This Example Exists

This example demonstrates how `include_thoughts` controls the reasoning behavior of thinking-capable models via OpenRouter. It runs a nested loop over two free-tier models and both `include_thoughts` values to show that the control works regardless of a model's default reasoning behavior.

### Why Two Models
**Problem**: OpenRouter models differ in whether they reason by default. `moonshotai/kimi-k2.6:free` shows its thinking process unless told otherwise, while `google/gemma-4-31b-it:free` stays silent unless reasoning is explicitly requested.

**Solution**: The example pairs these two models so you can see that `include_thoughts` behaves consistently across both. llm7shi absorbs the per-model differences, so `include_thoughts=True` produces a thinking process and `include_thoughts=False` skips it regardless of the model's default behavior.

### Reasoning On vs Off
**Problem**: Thinking-capable models perform an internal reasoning process before answering. This is useful for complex tasks but adds latency and cost for simple queries where reasoning is unnecessary.

**Solution**: Shows the difference between `include_thoughts=True` (default) and `include_thoughts=False`. Set it to `True` to see the reasoning process or `False` to skip it; llm7shi handles the provider-specific details for you.
