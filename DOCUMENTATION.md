# Documentation Guidelines

This project adopts a documentation structure that prioritizes **implementation rationale** over implementation details.

## Core Philosophy

### Focus on "Why"
- **WHY**: Record the reasons for implementation and problems solved
- **HOW**: Omit details that can be understood by reading the code

### Localize When Possible
- If a piece of rationale anchors to one specific spot in the code (a function, a line, a constant), put it there as a short comment instead of in the `.md`. Splitting attention between code and doc for a single-point decision costs more than it saves.
- Reserve the `.md` for rationale that cannot be localized to one spot: it spans multiple functions/files, describes cross-cutting architecture, compares alternatives at the module level, or is background/history with no single anchor.
- When editing existing code, check whether nearby `.md` content has become localizable and move it into a comment; don't let both copies drift.

### Two-Tier Documentation Structure
- **Module .md files**: Implementation rationale and design decisions that can't be localized to one spot in the code (for developers/maintainers)
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
- ✅ Reasons and background for implementation that span multiple functions/files
- ✅ Cross-cutting architectural rationale
- ✅ Why alternative approaches were not adopted, when the comparison isn't tied to one spot
- ✅ Project/module-level history and background

### What to Exclude
- ❌ Rationale that anchors to one specific function/line/constant — put that in a code comment instead
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

Rationale anchored to one function goes into the code as a short comment:
```python
def process_data(data: str) -> str:
    # normalize here: comparison/search downstream assumed varying case and whitespace, causing frequent mismatches
    return data.strip().lower()
```

Rationale spanning multiple call sites goes into the `.md`:
```markdown
# Data Processing Module

## Why This Implementation Exists

### Choice of Preprocessing Unification
**Problem**: Individual normalization at each input path would create inconsistencies and make maintenance difficult.

**Solution**: Centralized normalization in `process_data`, with architecture requiring all input paths to call it rather than normalizing locally.
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
1. For rationale tied to one specific spot in the code, write it as a short WHY comment there.
2. For rationale that spans multiple functions/files or is otherwise non-localizable, record it in the corresponding `.md` file (create it if needed).

### When Modifying Existing Features
1. Add change rationale as a code comment if it anchors to one spot, otherwise to the `.md` file.
2. Update or remove `.md` content if past design decisions have changed, and move it into a comment if it has become localizable.

### Review Checklist
- Is rationale placed where it anchors: a code comment for one spot, the `.md` for content spanning multiple locations?
- Are code examples excluded from the `.md`?
- Are design decision rationales explained, without duplicating between code and `.md`?

Following these guidelines ensures that project design philosophy is clearly transmitted and long-term maintainability is improved.