# utils.py - Utility Functions

## Why These Utilities Exist

These utility functions solve specific cross-cutting concerns that emerged while building the llm7shi library:

### Parameter Display (`do_show_params`)
**Problem**: When debugging LLM interactions, it's crucial to see exactly what parameters and content are being sent to the API. However, this display should be optional and cleanly formatted.

**Solution**: Created a unified parameter display function that formats both key-value parameters and content arrays consistently, with proper alignment and quote prefixes for content.

### Message Format Detection (`is_openai_messages`)
**Problem**: The library needed to support both simple `List[str]` format and OpenAI's message-based format, requiring reliable format detection with comprehensive validation.

**Solution**: Created a detection function that validates message structure including role/content keys, proper types, and valid role values (`system`, `user`, `assistant`). Raises clear errors for mixed formats or invalid messages.

### Message Format Conversion (`contents_to_openai_messages`)
**Problem**: The library needed to convert between simple content arrays and OpenAI's message-based format, while handling system prompts and avoiding redundant conversions.

**Solution**: Automatic conversion with format detection:
- For `List[str]`: converts to OpenAI format with system prompt as first message if provided
- For `List[Dict[str, str]]`: returns as-is if no system_prompt parameter, otherwise checks for conflicts and adds system message
- Conflict detection: raises error if system prompt provided in both messages and parameter

### Gemini Content Conversion with System Prompt Extraction (`openai_messages_to_contents`)
**Problem**: Gemini API uses `Content` objects with different role naming (`user`/`model`) instead of OpenAI's message format (`user`/`assistant`). Additionally, system prompts embedded in messages needed to be extracted for Gemini's `system_instruction` config parameter.

**Solution**: Single-pass conversion that simultaneously converts messages and extracts system prompt:
- Processes all messages in one loop for efficiency
- Role mapping: `user` → `user`, `assistant` → `model` (Gemini terminology)
- System prompt extraction: extracts and validates (raises error if multiple system messages found)
- Returns tuple: `(List[Content], system_prompt or None)` combining both conversion and extraction
- Eliminates need for separate extraction step, simplifying the workflow

### Parameter Display Enhancement (`do_show_params`)
**Problem**: The original parameter display function needed to support both simple string format and the new message format with role labels for better debugging.

**Solution**: Enhanced display logic that detects message format and shows role labels (e.g., `> [user]`, `> [assistant]`) for message arrays while maintaining backward compatibility with simple string display.

### Schema Compatibility (`add_additional_properties_false`, `inline_defs`)
**Problem**: Different LLM APIs have different schema requirements:
- OpenAI requires `additionalProperties: false` for strict mode
- Pydantic generates schemas with `$defs` references that OpenAI doesn't accept
- Title fields from Pydantic can cause validation issues
- Circular references in schemas can cause infinite recursion

**Solution**: Created transformation functions that modify schemas to meet each API's specific requirements while preserving the original structure. The `inline_defs` function includes circular reference detection to prevent infinite recursion and raises a `ValueError` when cycles are detected.

### Schema Description Extraction for Prompt Enhancement (`extract_descriptions`)
**Problem**: Some LLM systems ignore or don't properly utilize the `description` fields in JSON schemas, leading to poor structured output quality. To improve results, these descriptions need to be extracted and embedded directly into prompts as context.

**Solution**: Created a function that extracts all property descriptions from nested JSON schemas into a flat key-value mapping, enabling automatic prompt enhancement with schema context for systems that don't natively support schema descriptions.

### Client-Side Schema Description Prompting (`create_json_descriptions_prompt`)
**Problem**: Multi-provider applications needed a consistent way to ensure schema field meanings were conveyed to all LLM providers, particularly Ollama which completely ignores schema `description` fields. Manual extraction and prompt formatting was repetitive and error-prone.

**Solution**: Created a utility function that automatically extracts schema descriptions and formats them into standardized prompt text. This provides a client-side solution that works across all providers while maintaining user control over when enhanced prompts are applied. The implementation supports both JSON schema dictionaries and Pydantic models, making it compatible with the library's existing structured output features.


## Key Design Decisions

### Separation of Concerns
**Problem**: System prompt conflict checking could be centralized or distributed across provider functions.

**Solution**: Conflict detection is performed locally by each consumer (`_generate_with_gemini()` and `contents_to_openai_messages()`) rather than in a shared validation layer. This approach:
- Allows `_generate_with_*()` functions to be called directly without mandatory validation overhead
- Keeps validation close to where the decision matters
- Provides clear error messages in context

### Minimal Conversion Strategy
**Problem**: Message format conversion could eagerly normalize all inputs or perform minimal transformations.

**Solution**: Chose minimal conversion approach:
- When `contents` is already in OpenAI format and no `system_prompt` parameter is provided, return as-is (no copy, no transformation)
- Only perform transformations when necessary (format conversion or system prompt addition)
- Reduces unnecessary object creation and preserves original data when possible

### Format Detection First
All conversion functions begin with format detection (`is_openai_messages()`) to determine the appropriate processing path. This provides comprehensive validation before any transformations occur.

### Non-Destructive Operations
All schema transformation functions create copies rather than modifying input objects. This prevents unexpected side effects when the same schema is used multiple times.

### Recursive Processing
Schema transformations handle deeply nested structures automatically, ensuring that all objects (including those in arrays and nested properties) receive the necessary modifications.

### Conditional Output
The parameter display function respects file output settings, allowing it to be easily disabled for silent operation modes.

### Client-Side vs Automatic Enhancement
**Problem**: Schema description enhancement could be implemented automatically within provider-specific code, but this would reduce transparency and user control.

**Solution**: Chose explicit client-side implementation where users call `create_json_descriptions_prompt()` when needed. This approach maintains transparency about what additional instructions are being sent to models, provides flexibility for users who don't need description enhancement, and ensures consistent behavior across all providers rather than provider-specific automatic modifications.
