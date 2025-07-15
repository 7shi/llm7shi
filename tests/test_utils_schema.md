# test_utils_schema.py - Schema Processing Tests

## Why These Tests Exist

Testing schema processing functions required addressing specific multi-provider compatibility challenges:

### Schema Transformation Validation
**Problem**: The schema processing functions (`add_additional_properties_false`, `inline_defs`) perform complex recursive transformations that must preserve schema semantics while meeting API-specific requirements. These transformations are critical for multi-provider compatibility.

**Solution**: Extensive test cases covering nested structures, arrays, and edge cases to ensure transformations don't break schema validity or lose information.

### OpenAI Compatibility Requirements
**Problem**: OpenAI's structured output API requires `additionalProperties: false` on all object schemas, but many schema generation tools don't add this by default. Missing this property causes API failures.

**Solution**: The `add_additional_properties_false()` function recursively adds this property to all object schemas, with comprehensive tests ensuring it works for deeply nested structures while preserving existing schema properties.

### Schema Reference Flattening
**Problem**: Some LLM providers don't support JSON schema `$ref` references, requiring schemas to be "flattened" by inlining all definitions. This transformation must preserve semantic meaning while removing the reference structure.

**Solution**: The `inline_defs()` function recursively resolves all `$ref` references and removes the `$defs` section, with tests covering complex nesting scenarios and proper cleanup of title fields.

### Circular Reference Handling
**Problem**: JSON schemas can contain circular references, which the `inline_defs()` function needs to detect to avoid infinite loops during processing.

**Solution**: Explicit tests for circular reference detection to ensure the function fails gracefully with `ValueError` rather than hanging indefinitely, providing clear error messages about which schema definition contains the circular reference.

