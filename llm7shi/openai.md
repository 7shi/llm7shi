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

### gpt-oss Template Filter Support
**Problem**: Some OpenAI-compatible servers (particularly llama.cpp with gpt-oss template) emit special control tokens (`<|channel|>`, `<|message|>`, etc.) that separate reasoning process from final output, but these tokens would appear in raw output without filtering.

**Solution**: Integrated `GptOssTemplateFilter` from `monitor.py` that activates only for the exact model name `"llama.cpp/gpt-oss"`, parsing control tokens to separate thoughts (analysis channel) from final text (final channel) with real-time incremental display.

**Structured Output Behavior**: The filter is automatically disabled when `response_format` is specified in kwargs (structured output mode). llama.cpp server does not emit control tokens in JSON mode, instead returning direct JSON output only. This optimization avoids unnecessary filter processing. Note that in JSON mode, the separation between reasoning and final answer via control tokens is not available; users who want to capture reasoning should include dedicated fields (e.g., `reasoning`) in their JSON schema.

