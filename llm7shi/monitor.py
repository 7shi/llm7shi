"""Stream output monitor for detecting repetition and max length."""
from typing import Optional


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
    
    def __init__(self, converter, max_length=None, check_repetition=True):
        """Initialize the stream monitor.
        
        Args:
            converter: MarkdownStreamConverter instance for formatting output
            max_length: Maximum length of generated text (None for no limit)
            check_repetition: Whether to check for repetitive patterns
        """
        self.converter = converter
        self.max_length = max_length
        self.check_repetition = check_repetition
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