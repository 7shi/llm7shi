# statusline.py - Rich-Based Progress Display

## Why This Implementation Exists

Build-time and batch-processing scripts that call this library repeatedly (e.g. generating one file per item in a large corpus) need a live progress bar, not just streamed model output. This originated in a downstream project ([dante-corpus](https://github.com/7shi/dante-corpus)) as a subclass of `ConsoleStream` and was promoted into the library once it became clear the pattern — a Rich `Progress` bar coexisting with streamed LLM output — is generic enough to be reused by any script built on this library.

### Optional Dependency Instead of Core Dependency
**Problem**: Rich is a full-featured console rendering library, much heavier than the `colorama` used by the core `terminal.py` module. Making it a hard dependency would impose that weight on every user of the library, even those who never build a progress UI.

**Solution**: Rich is declared under the `statusline` extra in `pyproject.toml` rather than in the core dependencies. `llm7shi.statusline` is a separate module that is never imported by `llm7shi/__init__.py`, so `import llm7shi` never touches Rich; only code that explicitly does `from llm7shi.statusline import StatusLine` needs the extra installed (`llm7shi[statusline]`).

### Reusing ConsoleStream Rather Than Building a New Streaming Path
**Problem**: A live Rich `Progress` display and streamed model text both write to the terminal. Printing raw streamed chunks directly under an active progress bar causes visual corruption (the bar gets overwritten mid-line).

**Solution**: `StatusLineConsoleStream` subclasses `ConsoleStream` (see [terminal.md](terminal.md)) and overrides its `print`/`wait_retry`/`error` hooks to route through the same Rich `Console` that owns the progress bar, so the two never race for the terminal. Passing `status_line.stream` as `file=` to a streaming call is enough to make the two coexist.

### Retry Countdown as a Temporary Progress Row
**Problem**: The base `ConsoleStream.wait_retry` prints a `\r`-based countdown, which collides with an active Rich `Live` display the same way raw streamed text does.

**Solution**: `StatusLineConsoleStream.wait_retry` adds a temporary task to the active `Progress` (moved to the top of the task list) that fills forward while its displayed number counts down via the `remaining` field on `_MofNColumn`, then removes the task once the wait completes. When no progress bar is active, it falls back to the same plain countdown behavior as the base class.

### Process-Wide Elapsed Time Instead of Per-Task Time
**Problem**: Rich's built-in elapsed-time column measures time since each task was added, which resets for every new item in a batch and doesn't answer "how long has this script been running."

**Solution**: `_ProcessElapsedColumn` measures from a module-level `_PROCESS_START` timestamp captured at import time, giving a single running total for the whole process regardless of how many tasks come and go.
