# openrouter.py - OpenRouter Reasoning Control Example

## Why This Example Exists

This example demonstrates how `include_thoughts` controls the reasoning behavior of thinking-capable models via OpenRouter. The model used (`moonshotai/kimi-k2.6:free`) is a free tier model available without payment.

### Reasoning On vs Off
**Problem**: Thinking-capable models perform an internal reasoning process before answering. This is useful for complex tasks but adds latency and cost for simple queries where reasoning is unnecessary.

**Solution**: Shows the difference between `include_thoughts=True` (default) and `include_thoughts=False`. With `False`, the library sends `reasoning.enabled=False` to OpenRouter, which skips the reasoning process entirely — as opposed to `exclude: True`, which runs reasoning but hides the output from the response.
