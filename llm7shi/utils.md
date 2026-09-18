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

### File Locking as a Shared Primitive
**Problem**: `usage.py`'s `usage.jsonl` persistence needs to serialize concurrent readers/writers (e.g. parallel batch jobs appending usage records), and that need isn't specific to usage tracking - any future feature reading/rewriting a shared file from multiple processes would need the same retry-with-timeout `flock` logic.

**Solution**: `locked()` lives here rather than in `usage.py` so it's a general-purpose primitive, not something callers have to reach into `usage.py` to reuse. It locks the target file itself (no separate `.lock` file to leak if a process dies mid-write) and takes `retry_interval`/`timeout` as parameters rather than module-level constants, since a caller's acceptable wait varies by file and workload.

