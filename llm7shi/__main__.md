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
uv run -m llm7shi md <markdown-file>
```

The `usage` command wraps `llm7shi.usage`'s persistence helpers, with its own
`show`/`merge` subcommands (a second level of subparsers, since both need a
shared `-f/--file` option that `md` has no use for):

```
uv run -m llm7shi usage show [-a]
uv run -m llm7shi usage merge
```

`-f/--file` defaults to `find_usage_file()`'s upward search from the current
directory rather than a fixed path, since `llm7shi` itself has no notion of
"project root" (see `usage.md`).
