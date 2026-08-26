# gemma4.py - Same Model Across Multiple Providers

## Why This Example Exists

This example demonstrates that a single model can be accessed uniformly across multiple providers. It runs the same Gemma model (`gemma-4-31b-it`) through Google, OpenRouter, and Ollama, pairing each with both `include_thoughts` values to show that the unified interface holds regardless of where the model is hosted.

For the raw, unwrapped API code behind each provider — what llm7shi replaces — see [docs/20260608-provider-apis.md](../docs/20260608-provider-apis.md).
