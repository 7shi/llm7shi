from colorama import just_fix_windows_console, Fore, Style

# Fix Windows console to properly display ANSI color codes
just_fix_windows_console()

BOLD_ON = Style.BRIGHT + Fore.RED
BOLD_OFF = Style.NORMAL + Fore.RESET


def bold(text):
    """Convert text to Colorama bold format"""
    return BOLD_ON + text + BOLD_OFF


def convert_markdown(text):
    """Convert Markdown **bold** sections to Colorama bold (handles unclosed tags)"""
    result = ""
    # Normalize line endings to Unix style (LF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    bright_mode = False
    i = 0

    while i < len(text):
        # Check for ** markdown bold marker
        if i + 1 < len(text) and text[i:i+2] == "**":
            # Toggle bold state
            bright_mode = not bright_mode
            if bright_mode:
                result += BOLD_ON
            else:
                result += BOLD_OFF
            i += 2  # Skip both asterisks
        else:
            # Auto-close bold at newline if still open
            if bright_mode and text[i] == "\n":
                result += BOLD_OFF
                bright_mode = False
            # Append current character
            result += text[i]
            i += 1

    # Ensure bold is closed at end of text
    if bright_mode:
        result += BOLD_OFF

    return result


class MarkdownStreamConverter:
    """
    Class for incrementally converting **bold** text received in streams.
    When "*" is encountered, check if next is also "*" for bold toggle.
    Auto-close at newlines or end if not properly closed.
    """
    def __init__(self):
        self.buffer = ""  # Buffer for incomplete ** markers
        self.bright_mode = False  # Track current bold state

    def feed(self, chunk):
        """Process a chunk of streaming text and return converted output"""
        output = ""
        i = 0
        # Combine buffered text with new chunk
        text = self.buffer + chunk
        self.buffer = ""
        
        while i < len(text):
            # Check for ** markdown bold marker
            if i + 1 < len(text) and text[i:i+2] == "**":
                # Toggle bold state
                self.bright_mode = not self.bright_mode
                output += BOLD_ON if self.bright_mode else BOLD_OFF
                i += 2
            else:
                # If chunk ends with single *, buffer it for next chunk
                if text[i] == "*" and i + 1 == len(text):
                    self.buffer = "*"
                    break
                # Auto-close bold at newline
                if self.bright_mode and text[i] == "\n":
                    output += BOLD_OFF
                    self.bright_mode = False
                output += text[i]
                i += 1
        return output

    def flush(self):
        """Flush any remaining buffered content and reset state"""
        # Output any remaining single * in buffer
        output = self.buffer
        self.buffer = ""
        # Ensure bold is closed
        if self.bright_mode:
            output += BOLD_OFF
            self.bright_mode = False
        return output
