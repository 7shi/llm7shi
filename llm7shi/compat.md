# llm7shi/compat.py - LLM API Compatibility Layer

## Why This Exists

As the library evolved, we realized that different LLM providers have significant API differences that make it difficult to switch between them or test the same prompts across providers. This compatibility layer was created to address specific interoperability challenges:

### Unified Interface Need
**Problem**: OpenAI, Gemini, and Ollama have completely different API structures:
- OpenAI uses message arrays with role-based conversations
- Gemini uses content arrays with different parameter names
- Ollama uses message arrays similar to OpenAI but with different parameter names
- Each has different schema requirements for structured output

**Solution**: Created `generate_with_schema()` as a single function that abstracts these differences while preserving provider-specific features.

### Schema Format Incompatibilities  
**Problem**: The same Pydantic model generates different JSON schemas for different APIs:
- OpenAI requires `additionalProperties: false` for strict mode
- OpenAI doesn't support `$defs` references that Pydantic generates
- Gemini uses its own Schema object format
- Ollama uses `format` parameter with JSON schema directly

**Solution**: Implemented automatic schema transformations that convert between formats while preserving the original model structure.

### Feature Parity vs Specificity
**Problem**: Some features are provider-specific (like Gemini's and Ollama's thinking process), but we wanted a way to use them when available without breaking compatibility.

**Solution**: Made provider-specific parameters optional and ignored when not supported, allowing code to work across providers while leveraging unique features when available. For Ollama, the `include_thoughts` parameter is passed as `think` with automatic capability detection to prevent errors on models that don't support thinking.

### Multi-Format Message Support
**Problem**: Users needed a consistent way to handle both simple prompts and multi-turn conversations with conversation history:
- Simple use cases work well with `List[str]` format
- Multi-turn conversations require role-based message format like OpenAI's
- Gemini uses different Content objects while OpenAI/Ollama use message arrays
- System prompts could be provided both as parameter and embedded in messages, causing conflicts

**Solution**: Extended `generate_with_schema()` to accept both formats:
- `List[str]` - Legacy format for simple prompts (backward compatible)
- `List[Dict[str, str]]` - OpenAI-compatible message format with roles: `system`, `user`, `assistant`
- Automatic format detection via `is_openai_messages()` utility
- Role mapping: `assistant` → `model` for Gemini API compatibility
- System prompt conflict detection: raises error if provided in both messages and parameter
- Provider-specific handling: Gemini converts to Content objects, OpenAI/Ollama use messages directly

Example:
```python
# Multi-turn conversation with message format
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language."},
    {"role": "user", "content": "What makes it special?"}
]
response = generate_with_schema(messages, model="google:gemini-2.5-flash")

# Legacy format still works
response = generate_with_schema(
    ["What is Python?"],
    system_prompt="You are helpful.",
    model="google:gemini-2.5-flash"
)
```

## Key Design Decisions

### Vendor Prefix Model Detection
**Problem**: Users needed a clear way to specify which API to use while maintaining backward compatibility with existing model names.

**Solution**: Implemented vendor prefix support using regex pattern `([^:]+):(.*)` to parse model names:
- `"openai:gpt-4.1-mini"` → OpenAI API with `gpt-4.1-mini`
- `"google:gemini-2.5-flash"` → Gemini API with `gemini-2.5-flash`
- `"ollama:qwen3:4b"` → Ollama API with `qwen3:4b`
- Legacy patterns like `"gpt-4.1-mini"` and `"gemini-2.5-flash"` continue to work for backward compatibility
- Defaults to Gemini when no vendor prefix is specified

### Base URL Embedding in Model String
**Problem**: Users running OpenAI-compatible servers (llama.cpp, LocalAI, etc.) needed a way to specify custom endpoints without adding separate configuration parameters to every function call.

**Solution**: Extended model string format to support `@base_url` suffix using `rsplit("@", 1)` parsing:
- `"openai:gpt-4.1-mini@http://localhost:8080/v1"` → OpenAI API with custom endpoint
- `"openai:llama.cpp/gpt-oss@http://192.168.0.8:8080/v1"` → Custom server with gpt-oss template
- `"openai:gpt-4.1-mini@http://localhost:8080/v1|CUSTOM_API_KEY"` → OpenAI API with custom endpoint and custom API key from environment variable
- Base URL is extracted and passed to the underlying `generate_content()` function
- This approach keeps model selection and endpoint configuration in a single string parameter

**API Key Specification**: When using custom endpoints with `@base_url`, you can specify which environment variable contains the API key using `|api_key_env` syntax:

- **Without `|`**: Uses empty API key (secure default for local servers)
  - Example: `"openai:gpt-4@http://localhost:11434/v1"`
  - Security: Prevents leaking `OPENAI_API_KEY` to untrusted local servers

- **With `|api_key_env`**: Uses specified environment variable
  - Example: `"openai:gpt-4@http://my-proxy.com/v1|MY_PROXY_KEY"`
  - The value from `os.environ.get("MY_PROXY_KEY")` will be used
  - Use case: Authenticated proxy services or custom OpenAI-compatible APIs

**llama-server Design Pattern**: Since llama-server provides only one model at a time and ignores the model name parameter in API requests, the model name portion (e.g., `"llama.cpp/gpt-oss"`) serves as a client-side template identifier rather than selecting a specific model on the server. This design enables users to signal which prompt template parser should be activated (like `GptOssTemplateFilter`) based on the server's configuration, independent of which model is actually being served. The server address is specified via `@base_url`, while the model name controls client-side behavior such as filter activation.

### Response Object Unification
Extended the existing `Response` dataclass to work with all providers, ensuring the same fields are available regardless of which API was used.

### Non-Breaking Integration
The compatibility layer imports and uses existing library functions rather than reimplementing them. For OpenAI and Ollama support, it delegates to the optional `openai.py` and `ollama.py` modules while handling schema transformations and message conversion locally.

### Schema Transformation Pipeline
Created a series of transformation functions that modify schemas step-by-step to meet each API's requirements, making the process debuggable and extensible.

## Quality Control Integration

### Unified Stream Monitoring
**Problem**: OpenAI, Gemini, and Ollama implementations could have duplicated repetition detection and max length logic.

**Solution**: All providers use the shared `StreamMonitor` class (see [monitor.md](monitor.md)) for consistent quality control. The OpenAI and Ollama implementations are handled by the dedicated `openai.py` and `ollama.py` modules while maintaining the same monitoring capabilities.

## Schema Description Compatibility

### Provider-Specific Schema Handling
**Problem**: Different providers handle JSON schema `description` fields inconsistently:
- OpenAI and Gemini partially respect schema descriptions but may still misinterpret instructions
- Ollama completely ignores schema `description` fields, making structured output unreliable when field meanings are crucial

**Solution**: Rather than attempting automatic enhancement at the API level, we provide the `create_json_descriptions_prompt()` utility function (see [utils.md](utils.md)) that allows client-side explicit inclusion of schema descriptions in prompts. This approach maintains transparency and gives users control over when enhanced prompts are needed.

### Multi-Provider Structured Output Strategy
**Problem**: Applications requiring consistent structured output across providers faced reliability issues, particularly with models that needed explicit field explanations (like temperature unit conversions).

**Solution**: Adopted a client-side approach where users can explicitly extract and include schema descriptions in their prompts using `create_json_descriptions_prompt()`. This ensures all providers receive the same field explanations while maintaining the flexibility to omit them when not needed. The solution is documented in detail in [20250703-schema-descriptions.md](../docs/20250703-schema-descriptions.md).