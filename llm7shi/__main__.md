# __main__.py - `python -m llm7shi`

## Why This Implementation Exists

### Keeping `python -m llm7shi` After the Move to `cli/`
**Problem**: The command-line code moved to `llm7shi/cli/` (see
`cli/__init__.md`), but `python -m llm7shi` only works if the package has a
`__main__` module.

**Solution**: Keep `__main__.py` as a one-line forward to `llm7shi.cli.main`, so
both `python -m llm7shi` and the installed `llm7shi` command run the same
dispatcher.
