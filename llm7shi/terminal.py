from colorama import just_fix_windows_console, Fore, Back, Style

# Fix Windows console to properly display ANSI color codes
just_fix_windows_console()

BOLD_ON = Style.BRIGHT + Fore.RED
BOLD_OFF = Style.NORMAL + Fore.RESET

# Inline code (`...`) is rendered as bright blue foreground
CODE_ON = Style.BRIGHT + Fore.BLUE
CODE_OFF = Style.NORMAL + Fore.RESET

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

    Supports **bold** (bright red), inline `code` (bright blue), and fenced
    ``` code blocks ``` (the inner lines get a gray background, while the ```
    delimiter lines stay unshaded). A run of three or more backticks is treated
    as a code-fence delimiter rather than inline code.
    """
    result = ""
    # Normalize line endings to Unix style (LF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    bright_mode = False  # **bold**
    code_mode = False    # inline `code`
    code_block = False   # inside a ``` fenced block
    block_bg = False     # gray background active (block contents only)
    pending_nl = False   # a newline inside the block, held until the next token
    i = 0
    n = len(text)

    def release_pending():
        # Emit a held newline as block content: turn the background on (just
        # before the newline) if this is the first content line, then the newline
        nonlocal result, block_bg, pending_nl
        if pending_nl:
            if not block_bg:
                result += BLOCK_ON
                block_bg = True
            result += "\n"
            pending_nl = False

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
                    # Close the block: background OFF, then the held newline, so
                    # the closing ``` line stays unshaded
                    if block_bg:
                        result += BLOCK_OFF
                        block_bg = False
                    if pending_nl:
                        result += "\n"
                        pending_nl = False
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
                    code_mode = not code_mode
                    result += CODE_ON if code_mode else CODE_OFF
            i = j
            continue

        # Inside a code block everything else is literal. Newlines are held so we
        # can drop the background just before the one preceding the closing fence.
        if code_block:
            if ch == "\n":
                release_pending()  # flush a prior held newline as content
                pending_nl = True
            else:
                release_pending()
                result += ch
            i += 1
            continue

        # **bold** toggle
        if ch == "*" and i + 1 < n and text[i + 1] == "*":
            bright_mode = not bright_mode
            result += BOLD_ON if bright_mode else BOLD_OFF
            i += 2
            continue

        # Auto-close inline formatting at newline
        if ch == "\n":
            if code_mode:
                result += CODE_OFF
                code_mode = False
            if bright_mode:
                result += BOLD_OFF
                bright_mode = False
            result += ch
            i += 1
            continue

        result += ch
        i += 1

    # Ensure all formatting is closed at end of text
    release_pending()
    if code_mode:
        result += CODE_OFF
    if bright_mode:
        result += BOLD_OFF
    if block_bg:
        result += BLOCK_OFF

    return result


class MarkdownStreamConverter:
    """
    Class for incrementally converting Markdown received in streams.

    Handles **bold** (bright red), inline `code` (bright blue), and fenced
    ``` code blocks ``` (the inner lines get a gray background, the ``` delimiter
    lines stay unshaded). Incomplete markers at the end of a chunk (a lone "*" or
    a short backtick run that might still grow into a ``` fence) are buffered
    until the next chunk arrives. Inline formatting is auto-closed at newlines or
    on flush if not properly closed.
    """
    def __init__(self):
        self.buffer = ""  # Buffer for incomplete ** / ` markers
        self.bright_mode = False  # Track current bold state
        self.code_mode = False    # Track inline code state
        self.code_block = False   # Track fenced code block state
        self.block_bg = False     # Track block background (contents only)
        self.pending_nl = False   # Held newline inside a block (see feed)

    def _release_pending(self):
        """Emit a held in-block newline as content (background on before it)."""
        out = ""
        if self.pending_nl:
            if not self.block_bg:
                out += BLOCK_ON
                self.block_bg = True
            out += "\n"
            self.pending_nl = False
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
                        # Close the block: background OFF, then the held newline,
                        # so the closing ``` line stays unshaded
                        if self.block_bg:
                            output += BLOCK_OFF
                            self.block_bg = False
                        if self.pending_nl:
                            output += "\n"
                            self.pending_nl = False
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
                        self.code_mode = not self.code_mode
                        output += CODE_ON if self.code_mode else CODE_OFF
                i = j
                continue

            # Inside a code block everything else is literal. Newlines are held
            # so the background can be dropped just before the one preceding the
            # closing fence.
            if self.code_block:
                if ch == "\n":
                    output += self._release_pending()
                    self.pending_nl = True
                else:
                    output += self._release_pending()
                    output += ch
                i += 1
                continue

            # **bold** handling (buffer a lone trailing "*")
            if ch == "*":
                if i + 1 == n:
                    self.buffer = "*"
                    break
                if text[i + 1] == "*":
                    self.bright_mode = not self.bright_mode
                    output += BOLD_ON if self.bright_mode else BOLD_OFF
                    i += 2
                    continue
                output += ch
                i += 1
                continue

            # Auto-close inline formatting at newline
            if ch == "\n":
                if self.code_mode:
                    output += CODE_OFF
                    self.code_mode = False
                if self.bright_mode:
                    output += BOLD_OFF
                    self.bright_mode = False
                output += ch
                i += 1
                continue

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
                            output += "\n"
                            self.pending_nl = False
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
                        self.code_mode = not self.code_mode
                        output += CODE_ON if self.code_mode else CODE_OFF
            else:
                # Leftover lone "*" is literal
                output += buf

        # Flush a held in-block newline, then ensure all formatting is closed
        output += self._release_pending()
        if self.code_mode:
            output += CODE_OFF
            self.code_mode = False
        if self.bright_mode:
            output += BOLD_OFF
            self.bright_mode = False
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
