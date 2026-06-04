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

### Conservative Formatting
Auto-closes bold formatting at newlines to prevent formatting "bleed" into subsequent content. This ensures that unclosed markdown doesn't affect the entire terminal session.

### Minimal Scope
Focused on the markdown constructs that actually appear in LLM responses — `**bold**`, inline `` `code` ``, and ``` fenced code blocks ``` — rather than full markdown support. These are what matter for displaying LLM thinking processes, emphasis, and code.

### Inline Code vs Code Fences
**Problem**: A single backtick (`` `code` ``) denotes inline code, but a run of three or more backticks (` ``` `, typically at the start of a line) denotes a code fence. Treating every backtick as an inline toggle would corrupt fences.

**Solution**: Backticks are scanned as runs. A run of three or more is a fence delimiter that opens/closes a block; a single backtick toggles inline code. Inline code uses `CODE_ON = Style.BRIGHT + Fore.BLUE` (bright blue) and its backtick markers are removed, mirroring how `**bold**` is handled. For fenced blocks, only the **inner content lines** get a gray background (`BLOCK_ON = Back.LIGHTBLACK_EX`) — the ` ``` ` delimiter lines stay unshaded — so the code body is highlighted without the fence markers drawing attention. Markers inside the block are left untouched.

The background ON/OFF codes are emitted **just before the surrounding newline**, not after it: ON is placed right before the newline that ends the opening fence line, and OFF right before the newline that precedes the closing fence (e.g. `` ``` `` + `BLOCK_ON` + `\nbody` + `BLOCK_OFF` + `\n` + `` ``` ``). This keeps each shaded line ending clean across terminals. Implementing it requires holding one in-block newline until the next token is known, so the converter can decide whether that newline belongs to the block body or precedes the closing fence.

Sticking to Colorama constants keeps this cross-platform: Colorama only models the 16 standard ANSI colors, so 256-color/true-color backgrounds (which would be VT-dependent and untranslated on legacy Windows consoles) are intentionally avoided — `Back.LIGHTBLACK_EX` is the available gray. Because foreground (bold/inline) and background (fence) are independent ANSI channels, they compose without interfering. All four constants (`CODE_ON`/`CODE_OFF`/`BLOCK_ON`/`BLOCK_OFF`) are customizable, following the same base-color rationale as bold below.

### Bold Color Choice: `Style.BRIGHT + Fore.RED`
Bold text is rendered with `BOLD_ON = Style.BRIGHT + Fore.RED` rather than a single color constant like `Fore.LIGHTRED_EX`.

In most terminals, `Style.BRIGHT` (`\033[1m`) increases color intensity rather than rendering a bold font. This means `Style.BRIGHT + Fore.RED` produces the same visual result as `Fore.LIGHTRED_EX` (`\033[91m`). The two-part form was chosen intentionally: it expresses the intent as "bright red" (base color + intensity modifier) rather than hardcoding the pre-brightened variant, making the color customizable by changing only `Fore.RED`.