# Response Class

## Why This Design

The `Response` class was created to solve several data management challenges that emerged during LLM API interactions:

### Comprehensive Result Container
**Problem**: LLM API calls return various pieces of information beyond just the generated text - thinking processes, streaming chunks, configuration used, etc. Returning just a string loses valuable debugging and analysis data.

**Solution**: Created a dataclass that captures all aspects of the generation process while providing simple access to the most common use case (the generated text).

### Provider-Agnostic Design
**Problem**: Different LLM providers return different response formats and have different configuration objects. We needed a unified interface that could work with multiple providers.

**Solution**: Used generic `Any` types for provider-specific objects (`config`, `response`) while standardizing the common fields (`text`, `thoughts`, `model`).

### Simple Default Behavior
**Problem**: Most users just want the generated text, but having to access `response.text` for every call is verbose.

**Solution**: Implemented `__str__()` so that `print(response)` automatically shows the generated text, making the most common use case as simple as possible.

### Complete Audit Trail
**Problem**: When debugging LLM interactions or analyzing API behavior, you need access to the original inputs, all streaming chunks, and the raw API responses.

**Solution**: Preserved all data from the API interaction in the Response object, enabling post-processing, debugging, and analysis without needing to re-run expensive API calls.

### Repetition Detection Tracking
**Problem**: LLM outputs can sometimes fall into repetitive loops, wasting tokens and providing poor user experience. Users need to know when generation was stopped due to detected repetition patterns.

**Solution**: Added a `repetition` boolean field that tracks whether repetitive patterns were detected during generation, allowing users to distinguish between normal completion and early termination due to repetition.