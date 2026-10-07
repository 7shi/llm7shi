# cli/__init__.py - Command-Line Entry Point

## Why This Implementation Exists

The library needs a small command-line surface: eyeballing terminal formatting
(`md`), inspecting the shared usage log (`usage`), picking a model
(`models`), and trying one interactively (`chat`).

### A Separate `cli` Package
**Problem**: CLI code was spread across library modules (`__main__.py`, the
end of `usage.py`, a top-level `models.py`), so `llm7shi/` mixed modules meant
for import with code only the `llm7shi` command runs, and `argparse` leaked into
library modules.

**Solution**: All command-line code lives under `llm7shi/cli/`, one module per
subcommand that owns its own parser, with this module as the dispatcher. Library
modules keep only functions callers import; `llm7shi/__main__.py` remains only
so `python -m llm7shi` keeps working.

### Subcommand Dispatch
**Problem**: A single fixed behavior would be hard to extend, and a bare
positional file argument makes the command's intent unclear.

**Solution**: Use `argparse` subcommands so the entry point can grow over time.

### Forwarding Instead of Redefining Parsers
**Problem**: `cli/usage.py`'s CLI must also work as a standalone console-script
target in a downstream project (no `llm7shi` prefix). Defining its options here
as nested subparsers would mean keeping two copies in sync, and a downstream
script pointing at this `main()` would have to strip a leading `"usage"` off
`argv` first.

**Solution**: Each subcommand module owns a complete `main(argv, prog)`, and
this module forwards `argv[1:]` to it before the top-level parser runs, passing
`prog` so help shows `llm7shi usage` rather than a bare script name. `models`
and `chat` are forwarded the same way, so their options are defined only in
their own modules. The forwarded modules are imported on demand rather than at
package import, so running one with `python -m llm7shi.cli.usage` does not hit
runpy's "found in sys.modules" warning.

### Installed as the `llm7shi` Command
**Problem**: Separate console scripts per use (e.g. an `llm7shi-usage`) would
add one more name to `PATH` for every future command, and each would need its
own entry in `pyproject.toml`.

**Solution**: `pyproject.toml [project.scripts]` installs this module's `main()`
as a single `llm7shi` command, so a new subcommand added here is available
without further packaging changes. Since `md` is primarily a formatting check,
its help says so, while noting it also works as a simple Markdown viewer.
