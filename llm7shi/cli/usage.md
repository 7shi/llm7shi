# cli/usage.py - `llm7shi usage` Command

## Why This Implementation Exists

### A Complete CLI Usable as Its Own Console Script
**Problem**: The usage log is the one piece of `llm7shi` a downstream project is
likely to want as its *own* command (e.g. `usage = "llm7shi.cli.usage:main"` in
its `pyproject.toml [project.scripts]`). A subcommand nested in the `llm7shi`
dispatcher can't be pointed at directly by a console-script entry without a
wrapper to strip the leading `"usage"` token off `argv`.

**Solution**: This module defines its own complete `main()` (with `show`/`merge`
subcommands and `-f/--file`), so `argv` handed to it starts directly at
`show`/`merge`. `llm7shi usage` forwards its remaining `argv` here, so there is
exactly one parser definition either way. `main()` takes a `prog` argument so
`llm7shi usage -h` shows the name it was invoked by, while a downstream console
script keeps argparse's default (its own script name).

Registering the command in each downstream project stops scaling once several
projects share the same account-level `usage.jsonl`; installing llm7shi once as
a tool provides one `llm7shi usage` for all of them instead.

### Separate From the Library Module
**Problem**: The CLI used to live at the end of `usage.py`, mixing `argparse`
and printing into a module that downstream code imports for `Usage` and
`append_usage()`.

**Solution**: Keep the persistence and aggregation functions in `usage.py` and
only the command here. `usage.main` is kept as a thin forward so existing
`llm7shi.usage:main` console-script entries keep working.
