# Essay Evaluation Example

## Why This Implementation Exists

This example demonstrates automated essay evaluation using structured output generation, addressing the need for consistent and transparent AI-based assessment systems.

### Multi-Provider Comparison
**Problem**: Different LLM providers may have varying evaluation tendencies and biases, making it important to compare assessments across models.

**Solution**: Used the compat module's generate_with_schema to easily evaluate the same essay across cloud providers (Gemini, OpenAI) and local models (Ollama), revealing differences in evaluation approaches and scoring patterns between different model architectures.

### Intentionally Flawed Test Essay
**Problem**: Testing evaluation systems with well-written essays doesn't reveal whether the system can identify common writing flaws and logical fallacies.

**Solution**: Created a deliberately problematic essay with multiple issues (unsupported claims, ad hominem attacks, informal language) to verify the evaluation system's ability to detect and articulate specific weaknesses.