# statusline.py - Rich-Based Progress Display

## Why This Implementation Exists

Build-time and batch-processing scripts that call this library repeatedly (e.g. generating one file per item in a large corpus) need a live progress bar, not just streamed model output. This originated in a downstream project ([dante-corpus](https://github.com/7shi/dante-corpus)) as a subclass of `ConsoleStream` and was promoted into the library once it became clear the pattern — a Rich `Progress` bar coexisting with streamed LLM output — is generic enough to be reused by any script built on this library.

### Optional Dependency Instead of Core Dependency
**Problem**: Rich is a full-featured console rendering library, much heavier than the `colorama` used by the core `terminal.py` module. Making it a hard dependency would impose that weight on every user of the library, even those who never build a progress UI.

**Solution**: Rich is declared under the `statusline` extra in `pyproject.toml` rather than in the core dependencies, so only code that explicitly imports `llm7shi.statusline` needs it installed.
