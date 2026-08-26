# terminal.py - Terminal Formatting Utilities

## Why This Exists

When building CLI applications that display LLM responses, standard terminal output couldn't address streaming markdown formatting, incomplete text at chunk boundaries, or coexisting with a live progress bar.

## Key Design Decisions

### Minimal Scope
Focused on the markdown constructs that actually appear in LLM responses — `**bold**`, `*italic*`, inline `` `code` ``, and ``` fenced code blocks ``` — rather than full markdown support. These are what matter for displaying LLM thinking processes, emphasis, and code.

### Subclassing and Override Hooks (ConsoleStream)
`ConsoleStream` is designed as an extensible base class that developers can inherit and subclass to integrate output streams with advanced UI frameworks like `rich`. Rather than relying on fragile callback delegation, applications can subclass `ConsoleStream` and override specific hook methods to route and style outputs — see [statusline.md](statusline.md) for a built-in Rich-based implementation:

- `print(self, text: str, end: str)`: Hook for standard streaming chunk writes. Subclasses can override this to write directly to custom Rich panels or GUI text areas.
- `wait_retry(self, delay: int, message: str)`: Hook for the rate-limit retry countdown. Subclasses can override this to add, update, and remove countdown tasks inside `rich`'s progress bar contexts.
- `error(self, text: str)`: Hook for API errors or warning messages. Subclasses can override this to output styled error messages (such as applying `[red]` styling) or pop up alert dialogs.

This inheritance-based design decouples CLI UI orchestration from the core library, ensuring standard terminal outputs and custom Rich displays can coexist cleanly without layout corruption.