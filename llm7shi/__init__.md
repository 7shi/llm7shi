# llm7shi Package Initialization

## Why This Design

The `__init__.py` module was designed to solve specific package organization challenges:

### Convenient Public API
**Problem**: Users should be able to import commonly used functions directly from the package without needing to know internal module structure.

**Solution**: Created a curated `__all__` list that exports the most frequently used functions at the package level, while keeping implementation details in separate modules.

### Selective Export Strategy
**Problem**: Not all functionality should be part of the main API. Some modules (like `compat.py`) are for advanced use cases and shouldn't clutter the primary interface.

**Solution**: Explicitly chose which symbols to export. For example, `compat.py` requires explicit import (`from llm7shi.compat import generate_with_schema`) to keep it separate from the core API. Utility functions like `create_json_descriptions_prompt()` are exported at the package level because they solve common cross-provider compatibility issues that many users encounter.

### Dynamic Versioning
**Problem**: Hard-coding version numbers in source code creates maintenance overhead and sync issues with package metadata.

**Solution**: Used `importlib.metadata` to dynamically retrieve the version from package metadata, ensuring single source of truth.