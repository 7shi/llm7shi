"""Stream output monitor for detecting repetition and max length."""
from typing import Optional
import re


def _calculate_required_reps(pattern_len: int) -> int:
    """Calculate required repetitions for a given pattern length.
    
    Args:
        pattern_len: Length of the pattern to check
        
    Returns:
        int: Number of repetitions required for this pattern length
    """
    if pattern_len >= 31:
        return 10
    else:
        # Linear interpolation
        total_len = 100 + (pattern_len - 1) * 8
        return total_len // pattern_len


def detect_repetition(text: str, threshold: Optional[int] = None) -> bool:
    """Detect if text has repetitive patterns.
    
    Checks for patterns of 1-threshold characters that repeat based on
    pattern length: shorter patterns need more repetitions, longer patterns
    need fewer (minimum 10 repetitions for patterns >= 31 chars).
    
    Args:
        text: Text to check for repetitions
        threshold: Maximum pattern length to check (default: len(text)/10)
        
    Returns:
        bool: True if repetition detected, False otherwise
    """
    # Set default threshold based on text length
    if threshold is None:
        threshold = len(text) // 10
    # Check patterns from 1 to 10 characters
    for pattern_len in range(1, min(10, threshold) + 1):
        # Calculate required repetitions
        required_reps = _calculate_required_reps(pattern_len)
        
        # Break early if text is too short based on pattern length
        if pattern_len * required_reps > len(text):
            break
        
        # Extract pattern from the end
        pattern = text[-pattern_len:]
        
        # Check if text ends with required repetitions
        if text.endswith(pattern * required_reps):
            return True
    
    # Handle patterns > 10 characters
    if threshold <= 10:
        return False
    
    # For patterns > 10, they must contain the 10-char pattern
    # Use rfind optimization
    suffix_marker = text[-10:]  # Last 10 characters as a marker
    
    # Find all occurrences of suffix_marker and check patterns
    search_end = len(text) - 10
    min_search_pos = max(search_end - threshold, 0)
    while True:
        pos = text[:search_end].rfind(suffix_marker)
        
        # Stop if we've gone beyond the threshold limit
        if pos < min_search_pos:
            break
        
        # Extract the candidate pattern from this position to end
        candidate_pattern = text[pos + 10:]
        
        # Check if text ends with candidate_pattern repeated required times
        required_reps = _calculate_required_reps(len(candidate_pattern))
        if text.endswith(candidate_pattern * required_reps):
            return True
        
        # Continue searching before this position
        search_end = pos
    
    return False


class StreamMonitor:
    """Monitors streaming text output for repetition patterns and max length."""

    def __init__(self, converter, max_length=None, check_repetition=True, filter=None):
        """Initialize the stream monitor.

        Args:
            converter: MarkdownStreamConverter instance for formatting output
            max_length: Maximum length of generated text (None for no limit)
            check_repetition: Whether to check for repetitive patterns
            filter: Optional filter for processing content (e.g., GptOssTemplateFilter)
        """
        self.converter = converter
        self.max_length = max_length
        self.check_repetition = check_repetition
        self.filter = filter
        self.repetition_detected = False
        self.max_length_exceeded = None
        self.check_interval = 128  # Check trailing whitespace every 128 characters
        self.next_check = self.check_interval  # Initial whitespace check
        self.rep_check_interval = 4  # Check repetition every check_interval * 4 = 512 characters
        self.rep_check_count = 0  # Counter for repetition check frequency
    
    def check(self, text, file=None):
        """Check text for repetition and max length violations.
        
        Args:
            text: The accumulated text to check
            file: Optional file to write warning messages to
            
        Returns:
            bool: True if generation should continue, False if it should stop
        """
        # Check max_length first
        if self.max_length is not None and len(text) >= self.max_length:
            self.max_length_exceeded = self.max_length
            if file:
                print(self.converter.feed("\n\n⚠️ **Max length reached, stopping generation**\n"), file=file)
            return False
        
        # Check for repetition if enabled
        if self.check_repetition and len(text) >= self.next_check:
            # Check for trailing whitespace
            if len(text) - len(text.rstrip()) >= self.check_interval:
                self.repetition_detected = True
                if file:
                    print(self.converter.feed("\n\n⚠️ **Excessive whitespace detected, stopping generation**\n"), file=file)
                return False
            
            self.next_check += self.check_interval
            
            # Check for repetition every 512 characters
            self.rep_check_count += 1
            if self.rep_check_count >= self.rep_check_interval:
                if detect_repetition(text):
                    self.repetition_detected = True
                    if file:
                        print(self.converter.feed("\n\n⚠️ **Repetition detected, stopping generation**\n"), file=file)
                    return False
                self.rep_check_count = 0

        return True


class GptOssTemplateFilter:
    """Filter for parsing gpt-oss template format with channel-based output.

    Parses control tokens like <|channel|>analysis/final<|message|> to separate
    thoughts (analysis channel) from final text (final channel).
    """

    def __init__(self):
        """Initialize the filter."""
        self.thoughts = ""
        self.text = ""
        self.buffer = ""
        self.channel = None  # None, 'analysis', or 'final'
        self.expecting_channel_name = False  # True after <|channel|> token
        self.expecting_role_name = False  # True after <|start|> token

        # Control tokens to detect
        self.control_tokens = [
            '<|channel|>',
            '<|message|>',
            '<|start|>',
            '<|end|>',
        ]

    def feed(self, content: str) -> str:
        """Process content and extract thoughts/text based on channels.

        Args:
            content: Raw content chunk from stream

        Returns:
            str: Filtered content for display (final channel only)
        """
        self.buffer += content
        output = ""

        # Process buffer to detect control tokens and channel switches
        while self.buffer:
            # If we're expecting a role name, extract and discard it
            if self.expecting_role_name:
                # Common role names: 'assistant', 'user', 'system'
                role_names = ['assistant', 'user', 'system']
                role_found = False
                for role in role_names:
                    if self.buffer.startswith(role):
                        self.buffer = self.buffer[len(role):]
                        self.expecting_role_name = False
                        role_found = True
                        break

                if role_found:
                    continue
                else:
                    # Buffer might be too short, wait for more content
                    if any(role.startswith(self.buffer) for role in role_names):
                        break
                    else:
                        # Not a valid role name, treat as normal content
                        self.expecting_role_name = False

            # If we're expecting a channel name, extract it
            if self.expecting_channel_name:
                # Try to extract channel name
                if self.buffer.startswith('analysis'):
                    self.channel = 'analysis'
                    self.buffer = self.buffer[len('analysis'):]
                    self.expecting_channel_name = False
                    continue
                elif self.buffer.startswith('final'):
                    self.channel = 'final'
                    self.buffer = self.buffer[len('final'):]
                    self.expecting_channel_name = False
                    continue
                else:
                    # Buffer might be too short, wait for more content
                    # Check if buffer could be start of 'analysis' or 'final'
                    if ('analysis'.startswith(self.buffer) or
                        'final'.startswith(self.buffer)):
                        break
                    else:
                        # Not a valid channel name, treat as normal content
                        self.expecting_channel_name = False

            # Check for control tokens
            token_found = False
            for token in self.control_tokens:
                if self.buffer.startswith(token):
                    self.buffer = self.buffer[len(token):]
                    token_found = True

                    # Handle channel token
                    if token == '<|channel|>':
                        self.expecting_channel_name = True
                    elif token == '<|start|>':
                        self.expecting_role_name = True

                    break

            if token_found:
                continue

            # No control token found, process regular content
            # Look ahead to see if a control token is starting
            min_pos = len(self.buffer)
            for token in self.control_tokens:
                # Check if buffer might be starting a control token
                for i in range(1, min(len(token), len(self.buffer)) + 1):
                    if token.startswith(self.buffer[-i:]):
                        min_pos = len(self.buffer) - i
                        break

            if min_pos == 0:
                # Entire buffer might be start of a control token
                break

            # Extract content up to potential control token
            content_chunk = self.buffer[:min_pos]
            self.buffer = self.buffer[min_pos:]

            # Route to appropriate channel
            if self.channel == 'analysis':
                self.thoughts += content_chunk
            elif self.channel == 'final':
                self.text += content_chunk
                output += content_chunk
            else:
                # No channel set, assume it's final text
                self.text += content_chunk
                output += content_chunk

        return output

    def flush(self) -> str:
        """Flush any remaining buffer content.

        Returns:
            str: Any remaining filtered content
        """
        if self.buffer:
            output = ""
            if self.channel == 'final' or self.channel is None:
                self.text += self.buffer
                output = self.buffer
            elif self.channel == 'analysis':
                self.thoughts += self.buffer
            self.buffer = ""
            return output
        return ""