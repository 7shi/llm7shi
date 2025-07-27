# test_utils_repetition.py - Repetition Detection Tests

## Why These Tests Exist

Testing repetition detection required addressing a critical production problem with specific algorithmic challenges:

### Production Problem Validation
**Problem**: LLMs occasionally get stuck in infinite loops, generating repetitive output that wastes tokens and provides poor user experience. This was happening in real usage and needed automatic detection.

**Solution**: Comprehensive test suite validating the algorithm can detect various repetition patterns (single characters, words, phrases) while avoiding false positives on normal text.

### Algorithm Formula Verification  
**Problem**: The detection algorithm uses the formula `required_reps = threshold - pattern_len // 2` to scale repetition requirements. This mathematical relationship needed thorough validation to ensure it works correctly across pattern lengths.

**Solution**: Explicit tests for the formula with various pattern lengths and thresholds, ensuring shorter patterns require more repetitions (stricter detection) and longer patterns require fewer repetitions.

### End-of-Text Focus Testing
**Problem**: Repetition loops typically occur at the end of generated text, not in the middle. The algorithm needed to focus detection on text endings to avoid false positives from normal repetitive content within longer texts.

**Solution**: Specific tests verifying detection only triggers for patterns at text end, with mixed content scenarios to ensure middle repetitions don't trigger false alarms.

### Adaptive Threshold Testing
**Problem**: Fixed threshold values don't scale appropriately with text length - short texts need smaller search windows for efficiency, while long texts need larger windows for comprehensive detection.

**Solution**: Added `test_detect_repetition_adaptive_threshold()` to validate that when `threshold=None`, the function calculates `len(text) // 10` dynamically, ensuring optimal detection performance across varying text lengths while maintaining explicit threshold override capability.

### Performance and Integration Validation
**Problem**: The function runs every 1KB during LLM generation, so it must be fast and reliable. Any bugs could break ongoing generation or cause false stops.

**Solution**: Tests covering edge cases, boundary conditions, and various threshold values to ensure the algorithm is robust and performs consistently across different usage scenarios.