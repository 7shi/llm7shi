# terminal.py - Terminal Formatting Utilities

## Why This Exists

When building CLI applications that display LLM responses, we faced several specific challenges that standard terminal output couldn't address:

### Real-Time Markdown Formatting
**Problem**: LLM APIs stream responses with markdown formatting (like `**bold**` text), but terminals need ANSI escape codes for visual formatting. Converting after complete response arrival loses the real-time streaming effect.

**Solution**: Created a streaming converter that processes markdown in chunks as they arrive, maintaining formatting state across chunk boundaries.

### Robustness for Incomplete Text
**Problem**: Streaming text can be cut off mid-markdown marker (e.g., a chunk ending with just `*` when `**` is intended). Standard markdown parsers expect complete text.

**Solution**: Implemented intelligent buffering that holds incomplete markers until the next chunk arrives, plus auto-closing of unclosed formatting at line boundaries.

### Cross-Platform Terminal Support
**Problem**: Windows consoles historically didn't support ANSI escape codes, causing formatting to display as raw escape sequences.

**Solution**: Integrated Colorama's Windows console fixes and normalized line endings across platforms.

## Key Design Decisions

### Streaming-First Architecture
The `MarkdownStreamConverter` class maintains state between `feed()` calls, allowing continuous processing of text streams without losing formatting context.

### Newline Semantics: Soft Breaks vs Blank Lines
Inline formatting follows Markdown's line model. A single newline is a *soft* line break — the logical line (paragraph) continues, so active inline formatting **persists across it**. Inline formatting is reset only at a **blank line** (a paragraph break; a line containing only whitespace counts as blank) or at the end of text. This prevents unclosed markdown from bleeding into a *new paragraph* while still allowing a bold or code span to wrap naturally across a soft-wrapped line. A line is considered blank when no non-whitespace literal character has been emitted on it; the `**`/`` ` `` markers are consumed rather than emitted, so they don't count as content.

### Minimal Scope
Focused on the markdown constructs that actually appear in LLM responses — `**bold**`, inline `` `code` ``, and ``` fenced code blocks ``` — rather than full markdown support. These are what matter for displaying LLM thinking processes, emphasis, and code.

### Inline Code vs Code Fences
**Problem**: A single backtick (`` `code` ``) denotes inline code, but a run of three or more backticks (` ``` `, typically at the start of a line) denotes a code fence. Treating every backtick as an inline toggle would corrupt fences.

**Solution**: Backticks are scanned as runs. A run of three or more is a fence delimiter that opens/closes a block; a single backtick toggles inline code. Inline code uses `CODE_ON = Style.BRIGHT + Fore.BLUE` (bright blue) and its backtick markers are removed, mirroring how `**bold**` is handled. For fenced blocks, only the **inner content lines** get a gray background (`BLOCK_ON = Back.LIGHTBLACK_EX`) — the ` ``` ` delimiter lines stay unshaded — so the code body is highlighted without the fence markers drawing attention. Markers inside the block are left untouched.

The background ON/OFF codes are emitted **just before the surrounding newline**, not after it: ON is placed right before the newline that ends the opening fence line, and OFF right before the newline that precedes the closing fence (e.g. `` ``` `` + `BLOCK_ON` + `\nbody` + `BLOCK_OFF` + `\n` + `` ``` ``). This keeps each shaded line ending clean across terminals. Implementing it requires holding one in-block newline until the next token is known, so the converter can decide whether that newline belongs to the block body or precedes the closing fence. When the closing fence is indented, the leading whitespace on that line is also buffered alongside the held newline (`pending_indent`), so `BLOCK_OFF` is emitted before both the newline and the indent — ensuring the entire closing line, including its leading spaces, stays unshaded.

Sticking to Colorama constants keeps this cross-platform: Colorama only models the 16 standard ANSI colors, so 256-color/true-color backgrounds (which would be VT-dependent and untranslated on legacy Windows consoles) are intentionally avoided — `Back.LIGHTBLACK_EX` is the available gray. Because foreground (bold/inline) and background (fence) are independent ANSI channels, they compose without interfering. All four constants (`CODE_ON`/`CODE_OFF`/`BLOCK_ON`/`BLOCK_OFF`) are customizable, following the same base-color rationale as bold below.

### Nested Inline Formatting: A Stack, Not Two Flags
**Problem**: Inline elements share the single ANSI *foreground* channel, and each "off" code (`Style.NORMAL + Fore.RESET`) is a *full* reset. With independent on/off flags for `**bold**` and inline `` `code` ``, a nested span like `**bold `code` bold**` breaks: closing the inner code emits a full reset, which also clears the surrounding bold, leaving the trailing text uncolored.

**Solution**: Active inline formats are tracked as an ordered **stack** (`INLINE_ON` maps each format name to its on code). Opening a format pushes it and emits its on code; closing pops it, emits one `INLINE_OFF` reset, then **re-applies the remaining stack's on codes** so the surrounding (parent) element's formatting is restored. For the common single-level case the stack is empty after the pop, so the output is byte-identical to the old flag-based behavior — only genuinely nested closes differ. The `_open_inline`/`_close_inline`/`_close_all_inline` helpers are shared by both `convert_markdown()` and `MarkdownStreamConverter`, keeping one-shot and streaming output identical.

Because **markup inside inline code is left literal** (a `` ` `` span's contents are not re-parsed, so `**` inside it stays a literal asterisk), the stack only ever nests in one direction — `bold` then `code`, never the reverse. A general stack is still used rather than a special-case so that future inline elements compose the same way. The legacy `bright_mode`/`code_mode` attributes remain available as read-only properties derived from the stack (`"bold" in stack` / `"code" in stack`).

### Bold Color Choice: `Style.BRIGHT + Fore.RED`
Bold text is rendered with `BOLD_ON = Style.BRIGHT + Fore.RED` rather than a single color constant like `Fore.LIGHTRED_EX`.

In most terminals, `Style.BRIGHT` (`\033[1m`) increases color intensity rather than rendering a bold font. This means `Style.BRIGHT + Fore.RED` produces the same visual result as `Fore.LIGHTRED_EX` (`\033[91m`). The two-part form was chosen intentionally: it expresses the intent as "bright red" (base color + intensity modifier) rather than hardcoding the pre-brightened variant, making the color customizable by changing only `Fore.RED`.