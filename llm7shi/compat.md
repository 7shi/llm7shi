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

### Vendor Prefix Model Detection
**Problem**: Users needed a clear way to specify which API to use while maintaining backward compatibility with existing model names.

**Solution**: Implemented vendor prefix support using regex pattern `([^:]+):(.*)` to parse model names:
- `"openai:gpt-4o-mini"` → OpenAI API with `gpt-4o-mini`
- `"google:gemini-2.5-flash"` → Gemini API with `gemini-2.5-flash`
- Legacy patterns like `"gpt-4o-mini"` and `"gemini-2.5-flash"` continue to work for backward compatibility
- Defaults to Gemini when no vendor prefix is specified

### Response Object Unification
Extended the existing `Response` dataclass to work with both providers, ensuring the same fields are available regardless of which API was used.

### Non-Breaking Integration
The compatibility layer imports and uses existing library functions rather than reimplementing them. For OpenAI support, it delegates to the optional `openai.py` module while handling schema transformations and message conversion locally.

### Schema Transformation Pipeline
Created a series of transformation functions that modify schemas step-by-step to meet each API's requirements, making the process debuggable and extensible.

## Quality Control Integration

### Unified Stream Monitoring
**Problem**: OpenAI and Gemini implementations could have duplicated repetition detection and max length logic.

**Solution**: Both providers use the shared `StreamMonitor` class (see [monitor.md](monitor.md)) for consistent quality control. The OpenAI implementation is handled by the dedicated `openai.py` module while maintaining the same monitoring capabilities.