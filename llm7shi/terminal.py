from colorama import just_fix_windows_console, Fore, Back, Style

# Fix Windows console to properly display ANSI color codes
just_fix_windows_console()

BOLD_ON = Style.BRIGHT + Fore.RED
BOLD_OFF = Style.NORMAL + Fore.RESET

# Inline code (`...`) is rendered as bright blue foreground
CODE_ON = Style.BRIGHT + Fore.BLUE
CODE_OFF = Style.NORMAL + Fore.RESET

# Italic (*...*) is rendered as yellow foreground. Colorama has no direct italic
# support, so Fore.YELLOW stands in for it (no Style.BRIGHT, i.e. normal weight).
ITALIC_ON = Fore.YELLOW
ITALIC_OFF = Fore.RESET

# Inline (foreground) formatting is tracked as a stack so elements can nest
# (e.g. inline `code` inside **bold**). Each format maps to its ON code; OFF is
# a single generic foreground reset, after which the remaining stack's ON codes
# are re-applied to restore the surrounding (parent) formatting. The foreground
# is a single ANSI channel, so the innermost active format wins.
INLINE_ON = {"bold": BOLD_ON, "code": CODE_ON, "italic": ITALIC_ON}
INLINE_OFF = Style.NORMAL + Fore.RESET


def _open_inline(stack, fmt):
    """Push an inline format and return its ON code."""
    stack.append(fmt)
    return INLINE_ON[fmt]


def _close_inline(stack, fmt):
    """Pop an inline format, then re-apply the remaining stack's ON codes.

    Re-applying restores the parent element's formatting (e.g. closing inline
    code while still inside bold re-emits the bold ON code).
    """
    if fmt in stack:
        stack.remove(fmt)
    out = INLINE_OFF
    for f in stack:
        out += INLINE_ON[f]
    return out


def _close_all_inline(stack):
    """Clear the inline stack (blank line / end of text). One reset suffices."""
    if not stack:
        return ""
    stack.clear()
    return INLINE_OFF

# Fenced code block contents are rendered with a gray background (only the inner
# lines are shaded, not the ``` delimiter lines). Background ON/OFF is emitted
# just before the surrounding newline so each shaded line ends cleanly.
BLOCK_ON = Back.LIGHTBLACK_EX
BLOCK_OFF = Back.RESET


def bold(text):
    """Convert text to Colorama bold format"""
    return BOLD_ON + text + BOLD_OFF


def convert_markdown(text):
    """Convert Markdown to Colorama colors (handles unclosed tags)

    Supports **bold** (bright red), *italic* (yellow), inline `code` (bright
    blue), and fenced ``` code blocks ``` (the inner lines get a gray
    background, while the ``` delimiter lines stay unshaded). A run of three or
    more backticks is treated as a code-fence delimiter rather than inline code.
    A "*" only opens italic when followed by a non-space, so a "* " or indented
    "  * " list marker stays literal; a "*" that closes an open italic always
    closes it (regardless of the following character).

    Inline formats nest as a stack, so inline `code` inside **bold** restores
    the bold color once the code closes; markup inside inline code is left
    literal. A single (soft) newline keeps inline formatting active; a blank
    line (whitespace-only) or end of text resets it.
    """
    result = ""
    # Normalize line endings to Unix style (LF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    stack = []           # active inline formats (**bold**, inline `code`)
    line_has_content = False  # non-whitespace seen on the current line
    code_block = False   # inside a ``` fenced block
    block_bg = False     # gray background active (block contents only)
    pending_nl = False   # a newline inside the block, held until the next token
    pending_indent = ""  # whitespace after pending_nl, held to check for closing fence
    i = 0
    n = len(text)

    def release_pending():
        # Emit a held in-block newline (and any buffered indent) as content
        nonlocal result, block_bg, pending_nl, pending_indent
        if pending_nl:
            if not block_bg:
                result += BLOCK_ON
                block_bg = True
            result += "\n" + pending_indent
            pending_nl = False
            pending_indent = ""

    while i < n:
        ch = text[i]

        # Backtick run: inline code (single) vs code fence (three or more)
        if ch == "`":
            j = i
            while j < n and text[j] == "`":
                j += 1
            run = j - i
            if code_block:
                if run >= 3:
                    # Close the block: background OFF, then the held newline and
                    # indent (unshaded), so the closing ``` line stays unshaded
                    if block_bg:
                        result += BLOCK_OFF
                        block_bg = False
                    if pending_nl:
                        result += "\n" + pending_indent
                        pending_nl = False
                        pending_indent = ""
                    result += text[i:j]
                    code_block = False
                else:
                    # Literal backticks inside the block (content)
                    release_pending()
                    result += text[i:j]
            elif run >= 3:
                # Open a fenced block (the ``` delimiter line stays unshaded)
                result += text[i:j]
                code_block = True
                block_bg = False
                pending_nl = False
            else:
                # Inline code toggle (drop the backtick markers)
                for _ in range(run):
                    if "code" in stack:
                        result += _close_inline(stack, "code")
                    else:
                        result += _open_inline(stack, "code")
            i = j
            continue

        # Inside a code block everything else is literal. Newlines are held so we
        # can drop the background just before the one preceding the closing fence.
        # Leading whitespace after a held newline is also buffered so an indented
        # closing fence can be emitted unshaded.
        if code_block:
            if ch == "\n":
                release_pending()  # flush a prior held newline as content
                pending_nl = True
                pending_indent = ""
            elif pending_nl and (ch == " " or ch == "\t"):
                pending_indent += ch
            else:
                release_pending()
                result += ch
            i += 1
            continue

        # Inside inline code, other markup is suppressed (contents are literal);
        # only a backtick (handled above) can close it.
        code_active = bool(stack) and stack[-1] == "code"

        # **bold** / *italic* toggle. An open italic is always closed by a "*";
        # otherwise a "*" only opens italic when followed by a non-space, so a
        # "* " (or indented "  * ") list marker stays literal via the fall-through.
        if ch == "*" and not code_active:
            if i + 1 < n and text[i + 1] == "*":
                if "bold" in stack:
                    result += _close_inline(stack, "bold")
                else:
                    result += _open_inline(stack, "bold")
                i += 2
                continue
            if "italic" in stack:
                result += _close_inline(stack, "italic")
                i += 1
                continue
            if i + 1 < n and text[i + 1] != " ":
                result += _open_inline(stack, "italic")
                i += 1
                continue

        # Newline: a single (soft) newline keeps inline formatting; a blank line
        # (whitespace-only) dissolves the stack and resets formatting.
        if ch == "\n":
            if not line_has_content:
                result += _close_all_inline(stack)
            result += ch
            line_has_content = False
            i += 1
            continue

        if ch != " " and ch != "\t":
            line_has_content = True
        result += ch
        i += 1

    # Ensure all formatting is closed at end of text
    release_pending()
    result += _close_all_inline(stack)
    if block_bg:
        result += BLOCK_OFF

    return result


class MarkdownStreamConverter:
    """
    Class for incrementally converting Markdown received in streams.

    Handles **bold** (bright red), *italic* (yellow), inline `code` (bright
    blue), and fenced ``` code blocks ``` (the inner lines get a gray
    background, the ``` delimiter lines stay unshaded). A "*" only opens italic
    when followed by a non-space (so a "* " or indented "  * " list marker stays
    literal); a "*" closing an open italic always closes it. Incomplete markers
    at the end of a chunk (a
    lone "*" or a short backtick run that might still grow into a ``` fence) are
    buffered until the next chunk arrives. Inline formats nest as a stack (inline
    `code` inside **bold** restores bold when the code closes; markup inside
    inline code stays literal). Inline formatting persists across a soft newline
    and is reset at a blank (whitespace-only) line, on flush, or at end of text.
    """
    def __init__(self):
        self.buffer = ""  # Buffer for incomplete ** / ` markers
        self.stack = []           # Active inline formats (**bold**, inline `code`)
        self.line_has_content = False  # Non-whitespace seen on the current line
        self.code_block = False   # Track fenced code block state
        self.block_bg = False     # Track block background (contents only)
        self.pending_nl = False   # Held newline inside a block (see feed)
        self.pending_indent = ""  # Whitespace after pending_nl, held to check for closing fence

    @property
    def bright_mode(self):
        """Whether **bold** is currently active (derived from the stack)."""
        return "bold" in self.stack

    @property
    def code_mode(self):
        """Whether inline `code` is currently active (derived from the stack)."""
        return "code" in self.stack

    def _release_pending(self):
        """Emit a held in-block newline (and any buffered indent) as content."""
        out = ""
        if self.pending_nl:
            if not self.block_bg:
                out += BLOCK_ON
                self.block_bg = True
            out += "\n" + self.pending_indent
            self.pending_nl = False
            self.pending_indent = ""
        return out

    def feed(self, chunk):
        """Process a chunk of streaming text and return converted output"""
        output = ""
        i = 0
        # Combine buffered text with new chunk
        text = self.buffer + chunk
        self.buffer = ""
        n = len(text)

        while i < n:
            ch = text[i]

            # Backtick run: inline code vs code fence
            if ch == "`":
                j = i
                while j < n and text[j] == "`":
                    j += 1
                run = j - i
                # A short run at the very end may still grow into a ``` fence
                if j == n and run < 3:
                    self.buffer = text[i:j]
                    break
                if self.code_block:
                    if run >= 3:
                        # Close the block: background OFF, then the held newline
                        # and indent (unshaded), so the closing ``` line stays unshaded
                        if self.block_bg:
                            output += BLOCK_OFF
                            self.block_bg = False
                        if self.pending_nl:
                            output += "\n" + self.pending_indent
                            self.pending_nl = False
                            self.pending_indent = ""
                        output += text[i:j]
                        self.code_block = False
                    else:
                        output += self._release_pending()
                        output += text[i:j]
                elif run >= 3:
                    output += text[i:j]
                    self.code_block = True
                    self.block_bg = False
                    self.pending_nl = False
                else:
                    for _ in range(run):
                        if "code" in self.stack:
                            output += _close_inline(self.stack, "code")
                        else:
                            output += _open_inline(self.stack, "code")
                i = j
                continue

            # Inside a code block everything else is literal. Newlines are held
            # so the background can be dropped just before the one preceding the
            # closing fence. Leading whitespace after a held newline is also
            # buffered so an indented closing fence can be emitted unshaded.
            if self.code_block:
                if ch == "\n":
                    output += self._release_pending()
                    self.pending_nl = True
                    self.pending_indent = ""
                elif self.pending_nl and (ch == " " or ch == "\t"):
                    self.pending_indent += ch
                else:
                    output += self._release_pending()
                    output += ch
                i += 1
                continue

            # Inside inline code, other markup is suppressed (contents are
            # literal); only a backtick (handled above) can close it.
            code_active = bool(self.stack) and self.stack[-1] == "code"

            # **bold** / *italic* handling (buffer a lone trailing "*" until the
            # next char disambiguates ** vs * vs a "* " list marker)
            if ch == "*" and not code_active:
                if i + 1 == n:
                    self.buffer = "*"
                    break
                if text[i + 1] == "*":
                    if "bold" in self.stack:
                        output += _close_inline(self.stack, "bold")
                    else:
                        output += _open_inline(self.stack, "bold")
                    i += 2
                    continue
                # An open italic is always closed; otherwise "*" only opens italic
                # when followed by a non-space ("* "/"  * " list markers stay literal).
                if "italic" in self.stack:
                    output += _close_inline(self.stack, "italic")
                elif text[i + 1] != " ":
                    output += _open_inline(self.stack, "italic")
                else:
                    output += ch
                    self.line_has_content = True
                i += 1
                continue

            # Newline: a single (soft) newline keeps inline formatting; a blank
            # line (whitespace-only) dissolves the stack and resets formatting.
            if ch == "\n":
                if not self.line_has_content:
                    output += _close_all_inline(self.stack)
                output += ch
                self.line_has_content = False
                i += 1
                continue

            if ch != " " and ch != "\t":
                self.line_has_content = True
            output += ch
            i += 1

        return output

    def flush(self):
        """Flush any remaining buffered content and reset state"""
        output = ""
        # Resolve any buffered marker as a final (complete) token
        if self.buffer:
            buf = self.buffer
            self.buffer = ""
            if buf[0] == "`":
                run = len(buf)
                if self.code_block:
                    if run >= 3:
                        if self.block_bg:
                            output += BLOCK_OFF
                            self.block_bg = False
                        if self.pending_nl:
                            output += "\n" + self.pending_indent
                            self.pending_nl = False
                            self.pending_indent = ""
                        output += buf
                        self.code_block = False
                    else:
                        output += self._release_pending()
                        output += buf
                elif run >= 3:
                    output += buf
                    self.code_block = True
                    self.block_bg = False
                    self.pending_nl = False
                else:
                    for _ in range(run):
                        if "code" in self.stack:
                            output += _close_inline(self.stack, "code")
                        else:
                            output += _open_inline(self.stack, "code")
            else:
                # Leftover lone "*" from chunk end (EOF): close an open italic,
                # otherwise leave it literal (nothing follows it to open italic).
                if "italic" in self.stack:
                    output += _close_inline(self.stack, "italic")
                else:
                    output += buf

        # Flush a held in-block newline, then ensure all formatting is closed
        output += self._release_pending()
        output += _close_all_inline(self.stack)
        self.line_has_content = False
        if self.block_bg:
            output += BLOCK_OFF
            self.block_bg = False
        self.code_block = False
        return output


def render_file(path, chunk_size=8):
    """Render a Markdown file to the terminal for manual testing.

    The file is streamed through MarkdownStreamConverter in small chunks so the
    streaming code path (including markers split across chunk boundaries) is
    exercised the same way it is during live LLM output.
    """
    import sys

    with open(path, encoding="utf-8") as f:
        text = f.read()

    converter = MarkdownStreamConverter()
    for k in range(0, len(text), chunk_size):
        sys.stdout.write(converter.feed(text[k:k + chunk_size]))
    sys.stdout.write(converter.flush())
    sys.stdout.flush()
