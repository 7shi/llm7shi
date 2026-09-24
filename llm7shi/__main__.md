# __main__.py - Command-Line Entry Point

## Why This Exists

The library needs a small command-line surface for manually eyeballing terminal
formatting (e.g. rendering a Markdown file to verify bold, inline code, and code
fences look right).

### Subcommand Dispatch
**Problem**: A single fixed behavior would be hard to extend, and a bare
positional file argument makes the command's intent unclear.

**Solution**: Use `argparse` subcommands so the entry point can grow over time.
The first command, `md`, renders a Markdown file:

```
uv run llm7shi md <markdown-file>
```

### Delegating "usage" Instead of Redefining It
**Problem**: `usage.py`'s CLI (`show`/`merge` subcommands, its own `-f/--file`)
needs to work two ways: as `llm7shi usage ...` here, and as a
standalone console-script target in a downstream project (e.g.
`usage = "llm7shi.usage:main"`) with no `llm7shi` prefix. Defining its parser
here (a second level of subparsers under `usage`) would mean keeping two
copies in sync, and a downstream project pointing its own script at this
module's `main()` would have to strip a leading `"usage"` off `argv` first.

**Solution**: `usage.py` owns a complete `argparse` CLI itself (see `usage.md`)
and this module just forwards `argv[1:]` to `usage.main()` when `argv[0] ==
"usage"`, checked before the top-level parser runs rather than through a
nested subparser - `usage`'s own `-f`/`-a` flags and `show`/`merge` choices
never need to be declared twice this way:

```
uv run llm7shi usage show [-a]
uv run llm7shi usage merge
```

`usage.main()` receives `prog="llm7shi usage"` so its help shows the name it
was invoked by rather than a bare script name.

### Installed as the `llm7shi` Command
**Problem**: Separate console scripts per use (e.g. an `llm7shi-usage`) would
add one more name to `PATH` for every future command, and each would need
its own entry in `pyproject.toml`.

**Solution**: `pyproject.toml [project.scripts]` installs this module's
`main()` as a single `llm7shi` command, so `llm7shi usage ...` and
`llm7shi md ...` are available directly, and a new
subcommand added here is available without further packaging changes. Since
`md` is primarily a formatting check, its help says so, while noting it also
works as a simple Markdown viewer.
