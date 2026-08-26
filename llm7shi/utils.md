# utils.py - Utility Functions

## Why These Utilities Exist

These utility functions solve specific cross-cutting concerns that emerged while building the llm7shi library:

## Key Design Decisions

### Separation of Concerns
**Problem**: System prompt conflict checking could be centralized or distributed across provider functions.

**Solution**: Conflict detection is performed locally by each consumer (`_generate_with_gemini()` and `contents_to_openai_messages()`) rather than in a shared validation layer. This approach:
- Allows `_generate_with_*()` functions to be called directly without mandatory validation overhead
- Keeps validation close to where the decision matters
- Provides clear error messages in context

### Format Detection First
All conversion functions begin with format detection (`is_openai_messages()`) to determine the appropriate processing path. This provides comprehensive validation before any transformations occur.

### Non-Destructive Operations
All schema transformation functions create copies rather than modifying input objects. This prevents unexpected side effects when the same schema is used multiple times.

### Recursive Processing
Schema transformations handle deeply nested structures automatically, ensuring that all objects (including those in arrays and nested properties) receive the necessary modifications.

