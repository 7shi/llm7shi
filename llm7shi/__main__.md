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
