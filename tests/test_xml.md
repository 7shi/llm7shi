# XML Serialization Tests

## Why This Implementation Exists

To guarantee that chat history serialization is robust against syntax collisions in CDATA containers, we verify the symmetry and correctness of the escaping logic under various input patterns.

### Roundtrip Fidelity with CDATA Collision
**Problem**: The custom CDATA escape and unescape routines could introduce data loss or fail to restore original content like `]]>` properly if not explicitly verified.

**Solution**: Validated that input strings containing `]]>` are serialized without syntax errors, and that deserialization restores the exact original characters.

### Formatting Layout Verification (Flat Style)
**Problem**: Slight deviations in XML generation (such as unwanted indentation spaces or incorrect newline wrapping) can degrade raw log readability and break integration assumptions with downstream parsers.

**Solution**: Added strict line-by-line assertions for the serialized XML output to verify that tags are separated by newlines, CDATA content is properly wrapped, and no leading indentation spaces are generated.
