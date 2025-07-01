# utils.py - Utility Functions

## Why These Utilities Exist

These utility functions solve specific cross-cutting concerns that emerged while building the llm7shi library:

### Parameter Display (`do_show_params`)
**Problem**: When debugging LLM interactions, it's crucial to see exactly what parameters and content are being sent to the API. However, this display should be optional and cleanly formatted.

**Solution**: Created a unified parameter display function that formats both key-value parameters and content arrays consistently, with proper alignment and quote prefixes for content.

### Message Format Conversion (`contents_to_openai_messages`)
**Problem**: Our simple content array format needed to be converted to OpenAI's message-based format for API compatibility.

**Solution**: Automatic conversion that handles system prompts separately and treats all content items as user messages.

### Schema Compatibility (`add_additional_properties_false`, `inline_defs`)
**Problem**: Different LLM APIs have different schema requirements:
- OpenAI requires `additionalProperties: false` for strict mode
- Pydantic generates schemas with `$defs` references that OpenAI doesn't accept
- Title fields from Pydantic can cause validation issues

**Solution**: Created transformation functions that modify schemas to meet each API's specific requirements while preserving the original structure.

### Schema Description Extraction for Prompt Enhancement (`extract_descriptions`)
**Problem**: Some LLM systems ignore or don't properly utilize the `description` fields in JSON schemas, leading to poor structured output quality. To improve results, these descriptions need to be extracted and embedded directly into prompts as context.

**Solution**: Created a function that extracts all property descriptions from nested JSON schemas into a flat key-value mapping, enabling automatic prompt enhancement with schema context for systems that don't natively support schema descriptions.


## Key Design Decisions

### Non-Destructive Operations
All schema transformation functions create copies rather than modifying input objects. This prevents unexpected side effects when the same schema is used multiple times.

### Recursive Processing
Schema transformations handle deeply nested structures automatically, ensuring that all objects (including those in arrays and nested properties) receive the necessary modifications.

### Conditional Output
The parameter display function respects file output settings, allowing it to be easily disabled for silent operation modes.
