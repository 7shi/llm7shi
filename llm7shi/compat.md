# llm7shi/compat.py - LLM API Compatibility Layer

## Why This Exists

As the library evolved, we realized that different LLM providers have significant API differences that make it difficult to switch between them or test the same prompts across providers. This compatibility layer was created to address specific interoperability challenges:

### Unified Interface Need
**Problem**: OpenAI and Gemini have completely different API structures:
- OpenAI uses message arrays with role-based conversations
- Gemini uses content arrays with different parameter names
- Each has different schema requirements for structured output

**Solution**: Created `generate_with_schema()` as a single function that abstracts these differences while preserving provider-specific features.

### Schema Format Incompatibilities  
**Problem**: The same Pydantic model generates different JSON schemas for different APIs:
- OpenAI requires `additionalProperties: false` for strict mode
- OpenAI doesn't support `$defs` references that Pydantic generates
- Gemini uses its own Schema object format

**Solution**: Implemented automatic schema transformations that convert between formats while preserving the original model structure.

### Feature Parity vs Specificity
**Problem**: Some features are provider-specific (like Gemini's thinking process), but we wanted a way to use them when available without breaking compatibility.

**Solution**: Made provider-specific parameters optional and ignored when not supported, allowing code to work across providers while leveraging unique features when available.

## Key Design Decisions

### Simple Model Detection
Used model name prefixes for automatic API routing rather than explicit provider selection. This keeps the interface clean while being predictable.

### Response Object Unification
Extended the existing `Response` dataclass to work with both providers, ensuring the same fields are available regardless of which API was used.

### Non-Breaking Integration
The compatibility layer imports and uses existing library functions rather than reimplementing them. This ensures consistency and reduces maintenance burden.

### Schema Transformation Pipeline
Created a series of transformation functions that modify schemas step-by-step to meet each API's requirements, making the process debuggable and extensible.

## Stream Connection Management

### Investigation Results
During implementation of `max_length` truncation support, we investigated how to properly close streaming connections when stopping generation early:

**OpenAI Implementation**:
- ✅ Provides explicit `stream.close()` method
- ✅ Properly closes underlying HTTP connection via httpx
- ✅ Context manager support for automatic cleanup
- ✅ Can cancel ongoing streaming by calling `close()`

### Implementation Strategy
For OpenAI, we call `response.close()` when stopping due to max_length or repetition detection to properly release HTTP connections and ensure optimal resource management.

## Repetition Detection Optimization (2025-06-29)

Applied the same optimized detection strategy from `gemini.py` to the OpenAI implementation:

- **Pattern detection**: Every 512 characters (previously 1024) using the optimized algorithm
- **Whitespace detection**: Every 128 characters to catch excessive trailing whitespace (≥128 spaces)
- **Unified behavior**: Both Gemini and OpenAI APIs now use identical detection frequencies and thresholds

This ensures consistent quality control across providers while maintaining the performance benefits of the optimized algorithm.