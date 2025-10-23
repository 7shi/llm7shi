# Stream Monitor Module

## Why This Implementation Exists

This module was created to eliminate code duplication between Gemini and OpenAI streaming implementations while providing a unified approach to output quality control.

### Duplication in Stream Processing
**Problem**: Both `generate_content_retry` and `_generate_with_openai` contained identical logic for detecting repetition patterns and enforcing max length limits, leading to maintenance challenges and potential inconsistencies.

**Solution**: Extracted common monitoring logic into `StreamMonitor` class that encapsulates all output validation concerns, allowing both providers to share the same quality control implementation.

### Real-time Pattern Detection
**Problem**: LLMs can sometimes generate repetitive patterns or excessive whitespace during streaming, requiring immediate detection and interruption to avoid wasting tokens and time.

**Solution**: Implemented incremental checking that monitors output every 128 characters for whitespace and every 512 characters for repetition patterns, enabling early termination of problematic generations.

### Provider-agnostic Design
**Problem**: Different LLM providers have different streaming APIs and response structures, but output quality concerns are universal.

**Solution**: Designed `StreamMonitor` to be completely independent of provider-specific details, accepting only the accumulated text and returning a simple continue/stop decision.

## Detection Strategy (Moved from provider-specific implementations)

### Optimized Frequency Settings
**Problem**: Initial detection frequencies (every 1024 characters) were too slow to catch problems early, wasting tokens and time on problematic generations.

**Solution**: Optimized detection based on improved algorithm efficiency:
- **Pattern detection**: Every 512 characters using the optimized `detect_repetition` algorithm
- **Whitespace detection**: Every 128 characters for excessive trailing whitespace (≥128 spaces)
- **Rationale**: The optimized algorithm (see [docs/20250629-repetition-detection.md](../docs/20250629-repetition-detection.md)) is efficient enough to run more frequently without performance impact

### Stream Interruption Handling
**Problem**: Different providers have different mechanisms for closing streaming connections when stopping generation early.

**Solution**: `StreamMonitor` returns a simple boolean, letting each provider handle connection cleanup according to their specific requirements:
- **Gemini**: Simply break from the iterator loop (automatic cleanup)
- **OpenAI**: Call `response.close()` to properly release HTTP connections

## Repetition Detection Algorithm

### Pattern Recognition Challenge
**Problem**: Large language models occasionally get stuck in repetitive output loops, which wastes tokens and provides poor user experience. This was particularly noticeable during long generations.

**Solution**: Implemented a pattern detection algorithm that checks for repeating sequences at the end of generated text. The algorithm uses a two-phase approach optimized for performance while maintaining accuracy, with adaptive threshold calculation that scales with text length for optimal detection efficiency.

For detailed information about the algorithm, optimization strategy, and implementation details, see [Repetition Detection Algorithm](../docs/20250629-repetition-detection.md).

## Template Filter Integration

### gpt-oss Template Parsing Challenge
**Problem**: Some OpenAI-compatible servers (particularly llama.cpp with gpt-oss template) emit control tokens that structure the output into channels, mixing reasoning process with final answer in a single stream that needs real-time parsing.

**Solution**: Created `GptOssTemplateFilter` class that parses control tokens and separates content into appropriate channels during streaming, enabling clean separation of thoughts from final text without buffering the entire response.

**Design Context**: llama-server provides only one model at a time and ignores the model name in API requests. The filter activates based on the exact model name `"llama.cpp/gpt-oss"`, which serves as a client-side template identifier rather than an actual model name. This allows users to signal which template parser to use based on their server's prompt template configuration, independent of which model is actually being served.

### Control Token Protocol
**Problem**: The gpt-oss template uses multiple control tokens (`<|channel|>`, `<|message|>`, `<|start|>`, `<|end|>`) that can arrive split across multiple stream chunks, making naive string matching unreliable.

**Solution**: Implemented stateful buffer-based parsing that handles partial tokens across chunk boundaries:
- Maintains a buffer to handle tokens split across chunks
- Uses state machine pattern to track expectations (channel name, role name, content)
- Supports look-ahead to detect potential control token starts without premature output

### Channel-Based Content Routing
**Problem**: gpt-oss template directs content to different channels (`analysis` for reasoning, `final` for output), but the streaming API provides no built-in way to separate these logically distinct content types.

**Solution**: Implemented channel routing that accumulates content into separate properties:
- `thoughts` property: Accumulates all content from `analysis` channel
- `text` property: Accumulates all content from `final` channel
- `feed()` method returns only `final` channel content for display
- `flush()` method ensures remaining buffer content is properly routed

### Role Token Filtering
**Problem**: The `<|start|>` token is followed by role names (`assistant`, `user`, `system`) that are part of the protocol structure but should not appear in the final output.

**Solution**: Implemented role name detection and filtering that activates after `<|start|>` tokens, discarding the role name while allowing subsequent content to flow through normally.

### Incremental Display Support
**Problem**: Users expect real-time streaming output, but channel parsing requires buffering to detect control tokens, potentially delaying visible output.

**Solution**: Designed the filter to output `final` channel content immediately while only buffering enough to detect potential control token starts, ensuring minimal display latency while maintaining correct parsing.