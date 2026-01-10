# multiturn.py - Multi-Turn Conversation Example

## Why This Example Exists

This example demonstrates the multi-format message support that enables conversation history and multi-turn interactions across all LLM providers.

### Conversation History Need
**Problem**: Real-world applications often need to maintain context across multiple exchanges - chatbots remember previous questions, code assistants track ongoing discussions, and customer service systems build on earlier interactions. The simple `List[str]` format couldn't represent these multi-turn conversations.

**Solution**: Shows how to use OpenAI-compatible message format with role-based conversations (`system`, `user`, `assistant`) that works uniformly across Gemini, OpenAI, and Ollama, enabling applications to build conversational interfaces with full history support.

### System Prompt Integration
**Problem**: Applications need to set consistent behavior instructions (system prompts) while managing conversation history. Separating system prompts as a parameter creates two different mechanisms for what is fundamentally part of the conversation flow.

**Solution**: Demonstrates embedding system prompts directly in the message array as `role: "system"` messages, unifying prompt management and making conversation structure self-contained and portable across providers.

### Assistant Role Support
**Problem**: To build on previous responses or demonstrate desired behavior through examples (few-shot learning), applications need to include assistant messages in the conversation history. This wasn't possible with the legacy string array format.

**Solution**: Shows how `role: "assistant"` messages work across all providers, with automatic role mapping (assistant → model) for Gemini compatibility, enabling conversation continuity and example-based prompting.

### Provider-Neutral Multi-Turn
**Problem**: Each provider has different conversation formats - Gemini uses Content objects with user/model roles, OpenAI uses message arrays with user/assistant roles, and Ollama follows OpenAI's pattern. Building multi-turn applications required provider-specific code.

**Solution**: Provides a single message format that works identically across all three providers, abstracting the differences in role naming (assistant vs model) and message structure (Content objects vs dictionaries), so applications can focus on conversation logic rather than API compatibility.
