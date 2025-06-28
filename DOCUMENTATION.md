# Documentation Guidelines

This project adopts a documentation structure that prioritizes **implementation rationale** over implementation details.

## Core Philosophy

### Focus on "Why"
- **WHY**: Record the reasons for implementation and problems solved
- **HOW**: Omit details that can be understood by reading the code

### Two-Tier Documentation Structure
- **Module .md files**: Implementation rationale and design decisions (for developers/maintainers)
- **README.md files**: Usage instructions and practical information (for users)

## Module Documentation (*.md) Guidelines

### Target Files
Create `.md` files corresponding to each Python module:
- `module.py` → `module.md`
- `test_feature.py` → `test_feature.md`

### Required Structure
```markdown
# Module Name

## Why This Implementation Exists

Explain the background that led to this implementation and the specific problems it solves.

### Challenge 1 Name
**Problem**: Specific problem that was occurring
**Solution**: Adopted solution and its rationale

### Challenge 2 Name
**Problem**: Another challenge
**Solution**: Its solution
```

### What to Include
- ✅ Reasons and background for implementation
- ✅ Specific problems that were solved
- ✅ Rationale for important design decisions
- ✅ Reasons for architectural choices
- ✅ Why alternative approaches were not adopted

### What to Exclude
- ❌ Code examples and samples
- ❌ Detailed usage instructions and procedures
- ❌ API specifications and parameter descriptions
- ❌ Execution results and output examples
- ❌ Function and class behavior explanations

## README File Role

### Directory README.md Files
Provide practical information for users:
- Usage examples and sample code
- Setup procedures
- File structure explanations
- Execution instructions

### No Changes Required
README files maintain their traditional practical content and should not be modified under these guidelines.

## Implementation Examples

### Before (Traditional - Avoid)
```markdown
# Data Processing Module

## Function List

### process_data(data)
Normalizes string data.

**Parameters**:
- data (str): Target string for processing

**Return Value**:
- str: Normalized string

**Usage Example**:
```python
result = process_data("  Hello World  ")
print(result)  # "hello world"
```

Removes whitespace and converts to lowercase.
```

### After (Recommended)
```markdown
# Data Processing Module

## Why This Implementation Exists

### Need for Data Normalization
**Problem**: Input data from external sources varied in case and surrounding whitespace, causing frequent failures in comparison and search operations.

**Solution**: Adopted unified normalization processing at the input stage to stabilize all subsequent processing.

### Choice of Preprocessing Unification
**Problem**: Individual normalization at each processing point would create processing inconsistencies and make maintenance difficult.

**Solution**: Implemented centralized normalization through a single function, with architecture requiring all input paths to use this function.
```

## Implementation Tips

### 1. Think Problem-First
Start with "What problems would occur if this implementation didn't exist?" and work backwards

### 2. Record Decision-Making
Document the rationale for "Why did we choose B instead of A?"

### 3. Consider Future Developers
Write explanations that you or new team members can understand months later

### 4. Prioritize Conciseness
Explain each challenge in 1-3 sentences, avoiding verbosity

## Operational Rules

### When Adding New Features
1. Create corresponding `.md` file simultaneously with feature implementation
2. Clearly record implementation rationale
3. Document important design decisions

### When Modifying Existing Features
1. Add change rationale to `.md` file
2. Update if past design decisions have changed

### Review Checklist
- Is the implementation rationale clearly recorded?
- Are code examples excluded?
- Are design decision rationales explained?

Following these guidelines ensures that project design philosophy is clearly transmitted and long-term maintainability is improved.