# Stream Processing Module

## Why This Implementation Exists

As this library evolved from a single-provider wrapper for Gemini into a multi-provider library (supporting OpenAI and local Ollama), differences in error handling, connection management, and retry behavior led to inconsistent resilience and code duplication. 

This module provides a unified base class using the Template Method Pattern to standardise streaming consumption, repetition/length monitoring, error parsing, and rate-limit retry loops across all LLM providers.

### Challenge 1: Lack of Retry Consistency Across Providers
**Problem**: Only the Gemini client module supported robust retries with countdown displays for API rate limits (429) and server errors. Other providers (OpenAI, Ollama) had no retry capability, causing them to fail immediately on transient network drops or rate limits.

**Solution**: Centralised the streaming loop and retry logic into a generic base class (`StreamGenerator`). Each provider now defines a subclass implementing a provider-specific error handler, extending automatic retry resilience with colored countdowns uniformly to all providers.

### Challenge 2: Avoid Violation of Single Responsibility and Circular Dependencies
**Problem**: Placing retry/execution logic inside the `Response` data class would violate the Single Responsibility Principle, as `Response` is meant to be a pure data container. Alternatively, putting retry logic in `compat.py` would bypass scenarios where developers call the provider modules directly.

**Solution**: Created a dedicated `stream.py` module to encapsulate the execution orchestration. The `Response` class remains a pure container, and individual provider modules inherit from the base generator in `stream.py`, preserving clean module separation and direct module usage behaviors.

### Challenge 3: Verbose Callback passing vs. Subclassing
**Problem**: Using helper functions with callbacks required passing many arguments (like `model`, `config`, `contents`, and `file`) and required inner functions to capture the lexical scope.

**Solution**: Adopted the Template Method Pattern with class inheritance. All variables are held as instance attributes of the generator class, and provider-specific hook methods (like `make_stream`, `process_chunk`, and `handle_error`) are overridden, improving structure and code readability.
