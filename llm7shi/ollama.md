# Ollama Integration Module

## Why This Implementation Exists

### Need for Local Model Support
**Problem**: Users required access to locally-hosted LLMs through Ollama for privacy-sensitive applications and offline usage scenarios where cloud-based APIs were not suitable.

**Solution**: Created dedicated Ollama integration that mirrors the existing OpenAI and Gemini API patterns, ensuring consistent interface across all supported backends.

### API Consistency Requirement
**Problem**: Each LLM provider has different streaming response formats and chunk structures, creating fragmented user experience when switching between providers.

**Solution**: Adopted unified Response object structure and streaming patterns from existing modules, allowing seamless provider switching without changing user code.

### Thinking Process Visibility
**Problem**: Ollama's reasoning-capable models (like Qwen) expose thinking processes through `chunk.message.thinking`, but this valuable debugging information was not accessible to users.

**Solution**: Implemented thinking content extraction and display using the same visual formatting pattern as Gemini (🤔 **Thinking...** and 💡 **Answer:**), providing consistent UX across all thinking-capable models.

### Model Default Selection
**Problem**: Ollama supports numerous models but users needed a sensible default for getting started quickly without configuration overhead.

**Solution**: Selected Qwen3:4b as the default model due to its balance of performance, thinking capabilities, and reasonable resource requirements for local deployment.

### Capability-Aware Thinking Control
**Problem**: Not all Ollama models support thinking capabilities (e.g., Gemma3 models lack "thinking" in their capabilities), but users might request thinking mode without knowing model limitations.

**Solution**: Implemented automatic capability detection using `ollama.show()` to check model capabilities before enabling thinking mode. When `think=True` is requested but the model doesn't support thinking, the parameter is automatically set to `False` to prevent API errors while maintaining functionality.

### Structured Output Compatibility
**Problem**: Combining thinking mode with structured output (JSON format) caused malformed JSON responses due to Ollama API behavior, where extra characters were inserted at the beginning of responses.

**Solution**: Automatically disable thinking functionality when `format` parameter is present (structured output mode). This ensures JSON validity while preserving thinking capabilities for plain text generation. For detailed investigation and technical analysis, see [docs/20250702-ollama-thinking.md](../docs/20250702-ollama-thinking.md).