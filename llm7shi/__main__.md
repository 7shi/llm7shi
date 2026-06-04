# __main__.py - Command-Line Entry Point

## Why This Exists

The library needs a small command-line surface for manually eyeballing terminal
formatting (e.g. rendering a Markdown file to verify bold, inline code, and code
fences look right). The natural place for that would be running the relevant
submodule directly, but doing so causes a problem.

### Avoiding the runpy Warning
**Problem**: Running a submodule that the package already imports — e.g.
`python -m llm7shi.terminal` — triggers a `RuntimeWarning` from `runpy`:

> 'llm7shi.terminal' found in sys.modules after import of package 'llm7shi',
> but prior to execution of 'llm7shi.terminal'

This happens because `llm7shi/__init__.py` imports `terminal` (to export `bold`,
`convert_markdown`, etc.), so by the time `runpy` goes to execute it as
`__main__`, it is already loaded. Removing that import would break the public
API, and suppressing the warning is only a band-aid.

**Solution**: Put the entry point in `__main__.py` instead. `__init__.py` does
not import `__main__`, so `python -m llm7shi` (or `uv run -m llm7shi`) runs
cleanly with no warning. The CLI logic itself stays in `terminal.py`
(`render_file`); this module only dispatches to it.

### Subcommand Dispatch
**Problem**: A single fixed behavior would be hard to extend, and a bare
positional file argument makes the command's intent unclear.

**Solution**: Use `argparse` subcommands so the entry point can grow over time.
The first command, `md`, renders a Markdown file:

```
uv run -m llm7shi md <markdown-file>
```

`render_file` streams the file through `MarkdownStreamConverter` in small chunks,
exercising the same streaming code path used during live LLM output rather than a
one-shot conversion.
