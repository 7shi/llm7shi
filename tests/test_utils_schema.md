# test_utils_schema.py - Schema Processing Tests

## Why These Tests Exist

Testing schema processing functions required addressing specific multi-provider compatibility challenges:

### Schema Transformation Validation
**Problem**: The schema processing functions (`add_additional_properties_false`, `inline_defs`) perform complex recursive transformations that must preserve schema semantics while meeting API-specific requirements. These transformations are critical for multi-provider compatibility.

**Solution**: Extensive test cases covering nested structures, arrays, and edge cases to ensure transformations don't break schema validity or lose information.

