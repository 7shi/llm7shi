# OpenAI Module

## Why This Implementation Exists

### Separation of OpenAI-Specific Streaming Logic
**Problem**: The original `compat.py` module contained all OpenAI API handling logic mixed with schema processing, making the code difficult to maintain and reuse independently.

**Solution**: Extracted the core OpenAI streaming and monitoring functionality into a dedicated module that can be used independently or through the compatibility layer.

### Optional OpenAI Support Architecture
**Problem**: The main library focuses on Gemini API, but OpenAI support was embedded in the compatibility module, creating tight coupling and making it difficult to use OpenAI features independently.

**Solution**: Created a standalone OpenAI module that remains optional and is not included in default exports, allowing users to import it explicitly when needed while keeping the core library focused on Gemini.

### Clean Separation of Concerns
**Problem**: Schema handling and API-specific streaming logic were intermingled, making it difficult to modify or test each component independently.

**Solution**: Moved pure OpenAI streaming and monitoring logic to this module, leaving schema processing responsibilities in the compatibility layer where they belong conceptually.

### Pure API Interface Design
**Problem**: Message format conversion and parameter display logic would create unnecessary dependencies and reduce module independence.

**Solution**: Designed the module to accept pre-converted OpenAI messages format directly, establishing a policy where format conversion is the caller's responsibility, making this a pure OpenAI API wrapper.

### Dynamic Client Creation
**Problem**: Using a global client instance prevented support for custom endpoints (via `base_url`) and made testing more difficult due to singleton state management.

**Solution**: Changed from global client singleton to dynamic client creation per request, allowing `base_url` parameter to specify custom OpenAI-compatible endpoints while maintaining efficient resource usage through connection pooling at the HTTP level.

### Default Model Configuration
**Problem**: The OpenAI module required explicit model specification while the Gemini module provides a default model, creating inconsistent API design across the library.

**Solution**: Added `DEFAULT_MODEL = "gpt-4.1-mini"` constant and made the `model` parameter optional in `generate_content()` to match the pattern established in `gemini.py`, ensuring consistent user experience across both API modules.

### Custom Endpoint Support
**Problem**: Users wanted to connect to OpenAI-compatible endpoints (like llama.cpp server, LocalAI, or private deployments) without changing code structure.

**Solution**: Added optional `base_url` parameter to `generate_content()`, enabling seamless switching between OpenAI's official API and compatible alternatives while maintaining the same interface.

### gpt-oss Template Filter Support
**Problem**: Some OpenAI-compatible servers (particularly llama.cpp with gpt-oss template) emit special control tokens (`<|channel|>`, `<|message|>`, etc.) that separate reasoning process from final output, but these tokens would appear in raw output without filtering.

**Solution**: Integrated `GptOssTemplateFilter` from `monitor.py` that activates only for the exact model name `"llama.cpp/gpt-oss"`, parsing control tokens to separate thoughts (analysis channel) from final text (final channel) with real-time incremental display.

**Design Rationale**: The model name `"llama.cpp/gpt-oss"` serves as a template identifier rather than an actual model name. Since llama-server (llama.cpp's server component) provides only one model at a time and ignores the model name parameter in API requests, the model name string is repurposed as a client-side marker to activate the appropriate template filter. This design allows users to signal which template parser should be used based on the server's prompt template configuration, independent of the actual model being served.

### Thoughts Capture and Display
**Problem**: Models with reasoning capabilities (like those using gpt-oss template) emit both thinking process and final answer, but previous implementation discarded the thinking portion.

**Solution**: Extended response handling to capture and display thoughts separately with visual indicators (🤔 **Thinking...** / 💡 **Answer:**), matching the user experience pattern established in `gemini.py` and `ollama.py` for models with thinking capabilities.