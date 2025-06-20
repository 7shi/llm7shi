from colorama import just_fix_windows_console, Style

just_fix_windows_console()

def bold(text):
    """Convert text to Colorama bold format"""
    return Style.BRIGHT + text + Style.NORMAL

def convert_markdown(text):
    """Convert Markdown **bold** sections to Colorama bold (handles unclosed tags)"""
    result = ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")  # Convert line endings to LF
    bright_mode = False
    i = 0

    while i < len(text):
        # Search for **
        if i + 1 < len(text) and text[i:i+2] == "**":
            # Toggle style
            bright_mode = not bright_mode
            if bright_mode:
                result += Style.BRIGHT
            else:
                result += Style.NORMAL
            i += 2  # Skip 2 characters for **
        else:
            # Auto-close if newline found and not closed
            if bright_mode and text[i] == "\n":
                result += Style.NORMAL
                bright_mode = False
            # Add normal characters as-is
            result += text[i]
            i += 1

    # Auto-close if not closed
    if bright_mode:
        result += Style.NORMAL

    return result

class MarkdownStreamConverter:
    """
    Class for incrementally converting **bold** text received in streams.
    When "*" is encountered, check if next is also "*" for bold toggle.
    Auto-close at newlines or end if not properly closed.
    """
    def __init__(self):
        self.buffer = ""
        self.bright_mode = False

    def feed(self, chunk):
        output = ""
        i = 0
        text = self.buffer + chunk
        self.buffer = ""
        while i < len(text):
            # Detect "**"
            if i + 1 < len(text) and text[i:i+2] == "**":
                self.bright_mode = not self.bright_mode
                output += Style.BRIGHT if self.bright_mode else Style.NORMAL
                i += 2
            else:
                # Keep in buffer if ending with "*"
                if text[i] == "*" and i + 1 == len(text):
                    self.buffer = "*"
                    break
                # Auto-close at newline
                if self.bright_mode and text[i] == "\n":
                    output += Style.NORMAL
                    self.bright_mode = False
                output += text[i]
                i += 1
        return output

    def flush(self):
        # Output any remaining "*" in buffer
        output = self.buffer
        self.buffer = ""
        if self.bright_mode:
            output += Style.NORMAL
            self.bright_mode = False
        return output