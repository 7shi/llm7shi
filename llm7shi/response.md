# Response Class

## Why This Design

The `Response` class was created to solve several data management challenges that emerged during LLM API interactions:

### Comprehensive Result Container
**Problem**: LLM API calls return various pieces of information beyond just the generated text - thinking processes, streaming chunks, configuration used, etc. Returning just a string loses valuable debugging and analysis data.

**Solution**: Created a dataclass that captures all aspects of the generation process while providing simple access to the most common use case (the generated text).

### Complete Audit Trail
**Problem**: When debugging LLM interactions or analyzing API behavior, you need access to the original inputs, all streaming chunks, and the raw API responses.

**Solution**: Preserved all data from the API interaction in the Response object, enabling post-processing, debugging, and analysis without needing to re-run expensive API calls.
