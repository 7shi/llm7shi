# test_utils_repetition.py - Repetition Detection Tests

## Why These Tests Exist

Testing repetition detection required addressing a critical production problem with specific algorithmic challenges:

### Production Problem Validation
**Problem**: LLMs occasionally get stuck in infinite loops, generating repetitive output that wastes tokens and provides poor user experience. This was happening in real usage and needed automatic detection.

**Solution**: Comprehensive test suite validating the algorithm can detect various repetition patterns (single characters, words, phrases) while avoiding false positives on normal text.

### Algorithm Formula Verification
**Problem**: The detection algorithm uses a dynamic base algorithm with lookup table (base=340 for pattern lengths 1-20, fixed value of 20 for patterns ≥ 21 characters) to scale repetition requirements. This mathematical relationship needed thorough validation to ensure it works correctly across pattern lengths while maintaining monotonic non-decreasing behavior for early termination optimization.

**Solution**: Explicit tests for the formula with various pattern lengths and thresholds, ensuring shorter patterns require more repetitions (stricter detection) and longer patterns require fewer repetitions while maintaining coordination with weighted whitespace detection.

### End-of-Text Focus Testing
**Problem**: Repetition loops typically occur at the end of generated text, not in the middle. The algorithm needed to focus detection on text endings to avoid false positives from normal repetitive content within longer texts.

**Solution**: Specific tests verifying detection only triggers for patterns at text end, with mixed content scenarios to ensure middle repetitions don't trigger false alarms.

### Adaptive Threshold Testing
**Problem**: Fixed threshold values don't scale appropriately with text length - short texts need smaller search windows for efficiency, while long texts need larger windows for comprehensive detection.

**Solution**: Added `test_detect_repetition_adaptive_threshold()` to validate that when `threshold=None`, the function calculates `len(text) // 10` dynamically, ensuring optimal detection performance across varying text lengths while maintaining explicit threshold override capability.

### Performance and Integration Validation
**Problem**: The function runs every 1KB during LLM generation, so it must be fast and reliable. Any bugs could break ongoing generation or cause false stops.

**Solution**: Tests covering edge cases, boundary conditions, and various threshold values to ensure the algorithm is robust and performs consistently across different usage scenarios.

### Threshold Adjustment Validation
**Problem**: The original threshold (base=100) triggered false positives in production use, and when weighted whitespace detection was enhanced (threshold increased to 512), the repetition threshold became misaligned. Test values needed comprehensive updating to reflect the new dynamic base algorithm (base=340) while ensuring all detection behaviors remained correct.

**Solution**: Updated all test cases to reflect new threshold values (1-char: 340 reps, 5-char: 69 reps, 21+ chars: 20 reps) and verified that the algorithm maintains monotonic non-decreasing property for early termination optimization. All 145 tests continue to pass, validating that the threshold adjustment successfully reduces false positives while maintaining effective detection of genuine repetitive patterns.