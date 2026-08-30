# statusline.py - Rich-Based Progress Display

## Why This Implementation Exists

Build-time and batch-processing scripts that call this library repeatedly (e.g. generating one file per item in a large corpus) need a live progress bar, not just streamed model output. This originated in a downstream project ([dante-corpus](https://github.com/7shi/dante-corpus)) as a subclass of `ConsoleStream` and was promoted into the library once it became clear the pattern — a Rich `Progress` bar coexisting with streamed LLM output — is generic enough to be reused by any script built on this library.

### Optional Dependency Instead of Core Dependency
**Problem**: Rich is a full-featured console rendering library, much heavier than the `colorama` used by the core `terminal.py` module. Making it a hard dependency would impose that weight on every user of the library, even those who never build a progress UI.

**Solution**: Rich is declared under the `statusline` extra in `pyproject.toml` rather than in the core dependencies, so only code that explicitly imports `llm7shi.statusline` needs it installed.

### Subclassing Instead of Configuration Options
**Problem**: Downstream projects need bar variants the default layout doesn't cover — an extra elapsed-time column beside the label, or a different elapsed clock. Because `ProgressContext.__init__` built the column list inline, any such change meant reimplementing `__init__` end to end, and reusing the standard column formatting meant importing underscore-prefixed private names.

**Solution**: The extension surface is subclassing rather than configuration: column construction moved to `ProgressContext.columns()`, `StatusLine.progress_context_class` selects which context class `progress()` builds, and every column class the default layout uses is public. Keyword arguments on `progress()` naming *insertion points* ("a column here, a different elapsed column there") were considered and rejected: they would have fit the two known call sites and grown another option for every third one, whereas a single override point covers arbitrary layouts. `started_at` is a keyword argument nonetheless, because it is a value the run has rather than a knob on the layout — the caller knows when a run spanning several processes began and cannot express it any other way, while where its column lands stays the module's decision.
