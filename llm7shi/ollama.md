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