# API Key Security for Custom OpenAI-Compatible Endpoints

## Problem Discovery

When implementing support for custom OpenAI-compatible endpoints (llama.cpp, LocalAI, Ollama via OpenAI API, etc.), we discovered a critical security vulnerability in the naive implementation approach.

### The Security Risk

The OpenAI Python SDK has the following initialization behavior:

1. If `api_key` argument is not provided to `OpenAI()`, it automatically reads from `os.environ.get("OPENAI_API_KEY")`
2. The library **always sends the API key in the `Authorization` header** when making requests
3. Changing `base_url` alone does **not** prevent this automatic behavior

This creates a security risk where:
- **Information leakage**: If a user sets `base_url` to an untrusted server, their real `OPENAI_API_KEY` gets sent to that server
- **Plain text transmission**: Using `http://` (non-SSL) URLs could expose the API key to network packet capture
- **Local testing hazards**: Even connecting to `localhost` servers sends the production API key

### Code Evidence

From the OpenAI SDK source (`src/openai/_client.py`):

```python
@property
@override
def auth_headers(self) -> dict[str, str]:
    api_key = self.api_key
    if not api_key:
        # If api_key is empty (None or empty string), don't return headers
        return {}
    return {"Authorization": f"Bearer {api_key}"}
```

This shows that the only way to prevent the `Authorization` header from being sent is to explicitly set `api_key` to an empty value.

## Initial Implementation Problem

Our initial implementation in `llm7shi/openai.py` was:

```python
client = OpenAI(base_url=base_url) if base_url else OpenAI()
```

This meant:
- When `base_url` was specified, `api_key` was not provided
- The SDK automatically used `OPENAI_API_KEY` environment variable
- **Real API keys were sent to local/test servers by default**

## Solution Design

We needed a solution that:
1. **Defaults to secure behavior**: Prevents key leakage for local servers
2. **Supports authenticated endpoints**: Allows custom API keys when needed
3. **Maintains backward compatibility**: Standard OpenAI API usage unchanged
4. **Provides flexibility**: Users can specify which environment variable to use

### Design Decisions

#### Parameter Design

We added an `api_key_env` parameter (not `api_key` itself) because:
- Avoids passing raw API keys as string literals in code
- Follows the environment variable pattern used by the SDK
- Allows explicit control over which environment variable to read

#### Secure Default Behavior

When `base_url` is specified without `api_key_env`:
```python
client = OpenAI(base_url=base_url, api_key="")
```

This ensures:
- No `Authorization` header is sent (empty `api_key` triggers the skip in `auth_headers`)
- Safe for local servers (Ollama, llama.cpp, LocalAI) that don't require authentication
- Explicit opt-in required for sending credentials to custom endpoints

#### Three-Tier Logic

```python
if api_key_env is not None:
    # Explicit environment variable specified
    api_key = os.environ.get(api_key_env, "")
    client = OpenAI(base_url=base_url, api_key=api_key)
elif base_url is not None:
    # Custom endpoint without api_key_env: secure default
    client = OpenAI(base_url=base_url, api_key="")
else:
    # Standard OpenAI API: use SDK default behavior
    client = OpenAI()
```

## Syntax Extension for User-Facing API

The `compat.py` module already supported `model@base_url` syntax for custom endpoints. We extended it to support API key environment variable specification.

### Syntax Evaluation

We considered three options:

#### Option 1: `$` Delimiter
```
model@base_url$ENV_VAR
```
- ✅ Visually indicates environment variable (shell convention)
- ❌ Requires quoting in shell (prevents expansion)
- ⚠️ Can appear in URL query parameters

#### Option 2: `|` Delimiter (Selected)
```
model@base_url|ENV_VAR
```
- ✅ Minimal URL conflict risk
- ✅ Simple parsing (same complexity as `$`)
- ✅ Short and clean syntax
- ❌ Requires quoting in shell (pipe interpretation)

#### Option 3: `?` Query Parameter Style
```
model@base_url?api_key_env=ENV_VAR
```
- ✅ Most explicit and self-documenting
- ✅ Extensible for future parameters
- ❌ Longer syntax
- ❌ More complex parsing
- ⚠️ Conflicts with URLs that have query parameters

**Decision**: We chose `|` delimiter for simplicity and minimal conflict risk.

### Parsing Implementation

In `llm7shi/compat.py` (`_generate_with_openai` function):

```python
# Extract base_url and api_key_env from model if present
# Format: model@base_url|api_key_env
base_url = None
api_key_env = None
if model and "@" in model:
    model, url_rest = model.rsplit("@", 1)
    # Check for api_key_env specification
    if "|" in url_rest:
        base_url, api_key_env = url_rest.split("|", 1)
    else:
        base_url = url_rest
```

Key parsing features:
- Uses `rsplit("@", 1)` to handle colons in model names (e.g., `ollama:qwen3:4b`)
- Uses `split("|", 1)` for the API key environment variable name
- Backward compatible: `model@base_url` without `|` still works (defaults to empty API key)

## Usage Examples

### Local Server (No Authentication)
```python
from llm7shi.compat import generate_with_schema

response = generate_with_schema(
    ["Hello, world!"],
    model="openai:gpt-4@http://localhost:11434/v1"
)
```
Result: Empty `api_key=""` sent, no credentials leaked.

### Authenticated Custom Endpoint
```bash
export MY_PROXY_KEY="proxy-api-key-123"
```

```python
response = generate_with_schema(
    ["Hello, world!"],
    model="openai:gpt-4@http://my-proxy.com/v1|MY_PROXY_KEY"
)
```
Result: Value from `MY_PROXY_KEY` environment variable sent.

### Standard OpenAI API
```python
response = generate_with_schema(
    ["Hello, world!"],
    model="openai:gpt-4.1-mini"
)
```
Result: Standard SDK behavior, uses `OPENAI_API_KEY` environment variable.

### OpenAI-Compatible Vendor Prefixes
```bash
export OPENROUTER_API_KEY="sk-or-..."
export GROQ_API_KEY="gsk_..."
export XAI_API_KEY="xai-..."
```

```python
# OpenRouter with default model
response = generate_with_schema(
    ["Hello, world!"],
    model="openrouter:"
)
# Automatically uses: qwen/qwen3-4b:free@https://openrouter.ai/api/v1|OPENROUTER_API_KEY

# Groq with specific model
response = generate_with_schema(
    ["Hello, world!"],
    model="groq:llama-3.3-70b-versatile"
)
# Automatically uses: llama-3.3-70b-versatile@https://api.groq.com/openai/v1|GROQ_API_KEY

# X.AI Grok
response = generate_with_schema(
    ["Hello, world!"],
    model="grok:grok-4-1"
)
# Automatically uses: grok-4-1@https://api.x.ai/v1|XAI_API_KEY
```
Result: Pre-configured vendor prefixes automatically apply secure base_url and api_key_env settings, building on the security foundation established by this feature.

## Implementation Summary

### Modified Files

1. **llm7shi/openai.py**:
   - Added `api_key_env` parameter to `generate_content()`
   - Implemented three-tier API key selection logic
   - Added security documentation in docstring

2. **llm7shi/compat.py**:
   - Extended model string parsing to handle `|api_key_env` syntax
   - Passed `api_key_env` parameter to `generate_content()`

3. **tests/test_compat_vendor.py**:
   - Added `TestBaseUrlAndApiKeyEnvParsing` test class
   - 6 comprehensive test cases covering all scenarios

### Documentation Updates

1. **README.md**: Added security feature to feature list and setup section
2. **llm7shi/README.md**: Updated module descriptions and examples
3. **llm7shi/compat.md**: Added detailed API key specification section
4. **llm7shi/openai.md**: Added secure API key management section
5. **tests/test_compat_vendor.md**: Added base URL and API key parsing section

## Testing

All 156 tests pass, including 6 new tests specifically for this feature:

- `test_model_with_base_url_only`: Verifies `base_url` without `api_key_env` → `api_key_env=None`
- `test_model_with_base_url_and_api_key_env`: Verifies full `model@base_url|api_key_env` parsing
- `test_model_without_base_url`: Verifies standard model without custom endpoint
- `test_base_url_with_port`: Verifies URL with port (e.g., `http://192.168.0.8:8080/v1`)
- `test_empty_api_key_env`: Verifies `model@base_url|` with trailing pipe
- `test_api_key_env_with_underscores`: Verifies realistic environment variable names

## Security Impact

This implementation:
- ✅ **Prevents accidental key leakage** to local test servers
- ✅ **Enables authenticated custom endpoints** when needed
- ✅ **Maintains backward compatibility** with existing code
- ✅ **Follows principle of least privilege** (secure by default)
- ✅ **Clear opt-in mechanism** for sending credentials

## Building on This Foundation: OpenAI-Compatible Vendor Prefixes

The security infrastructure established by `api_key_env` and `model@base_url|api_key_env` syntax enabled a natural extension: pre-configured vendor prefixes for popular OpenAI-compatible providers.

### Implementation (Added Later)

Three vendor prefixes were added to `compat.py`:
- `openrouter:` - OpenRouter API
- `groq:` - Groq API
- `grok:` - X.AI Grok API

Each vendor has pre-configured:
- Default base_url (e.g., `https://openrouter.ai/api/v1`)
- Default api_key_env (e.g., `OPENROUTER_API_KEY`)
- Default model (e.g., `qwen/qwen3-4b:free`)

### Automatic Security Application

When a user specifies `model="openrouter:llama-3.3-70b"`, the system automatically constructs:
```
llama-3.3-70b@https://openrouter.ai/api/v1|OPENROUTER_API_KEY
```

This automatic construction:
1. ✅ Reuses the secure `@base_url|api_key_env` parsing logic
2. ✅ Applies secure defaults (empty API key if user hasn't set the environment variable)
3. ✅ Allows user overrides (if user specifies `@`, vendor defaults aren't applied)
4. ✅ Maintains the same security guarantees

### Why This Extension Works

The vendor prefix feature could be implemented cleanly because:
- The security-first defaults were already established
- The `|api_key_env` syntax provided explicit environment variable selection
- The parsing logic in `_generate_with_openai()` handled the transformed model string transparently
- User overrides naturally took precedence over vendor defaults

This demonstrates how a well-designed security foundation enables convenient features without compromising safety.

## Future Considerations

### Potential Extensions

1. **Direct API key parameter**: Consider adding `api_key` (not just `api_key_env`) for cases where keys come from non-environment sources
2. **Per-request headers**: Support for custom headers beyond just Authorization
3. **Credential helpers**: Integration with system credential stores

### Not Implemented (By Design)

1. **Automatic base_url from core vendor prefixes**: We don't automatically infer base_url for core vendors like `ollama:` (which could point to `localhost:11434`), preferring explicit configuration. However, OpenAI-compatible vendors (`openrouter:`, `groq:`, `grok:`) do have pre-configured base_url since they always point to the same public endpoints.
2. **Config file support**: Environment variables are sufficient for current use cases
3. **API key validation**: Left to the SDK/server to report invalid credentials

## Lessons Learned

1. **Security defaults matter**: The naive implementation would have leaked keys
2. **Environment variables are APIs**: They're part of the public interface
3. **Simple syntax wins**: `|` delimiter is concise and unambiguous
4. **Document security implications**: Users need to understand the risks
5. **Test edge cases thoroughly**: URL parsing has many corner cases (ports, special chars, etc.)
6. **Good foundations enable extensions**: The OpenAI-compatible vendor prefix feature was implemented cleanly because the security infrastructure (`api_key_env` parameter and secure defaults) was already in place. Designing for security first made convenience features safer to add.
