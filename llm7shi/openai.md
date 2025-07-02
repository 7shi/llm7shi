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

### Global Client Management
**Problem**: Creating a new OpenAI client instance for each API call would be inefficient and inconsistent with the library's pattern established in the Gemini module.

**Solution**: Implemented a global client instance at module level, matching the pattern used in `gemini.py` for consistent resource management and efficient connection reuse across multiple API calls.

### Default Model Configuration
**Problem**: The OpenAI module required explicit model specification while the Gemini module provides a default model, creating inconsistent API design across the library.

**Solution**: Added `DEFAULT_MODEL = "gpt-4.1-mini"` constant and made the `model` parameter optional in `generate_content()` to match the pattern established in `gemini.py`, ensuring consistent user experience across both API modules.