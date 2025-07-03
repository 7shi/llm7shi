# Essay Evaluation Example

## Why This Implementation Exists

This example demonstrates automated essay evaluation using structured output generation, addressing the need for consistent and transparent AI-based assessment systems.

### Dynamic Schema Generation from Criteria
**Problem**: Hard-coding evaluation schemas makes it difficult to modify or extend evaluation criteria, and maintaining consistency between prompts and schemas becomes error-prone.

**Solution**: Implemented dynamic generation of both JSON schema and prompts from a single CRITERIA dictionary, ensuring consistency and enabling easy modification of evaluation criteria.

### Reasoning-First Evaluation Order
**Problem**: When models generate scores before reasoning, they tend to make snap judgments and then rationalize them post-hoc, leading to less thoughtful evaluations.

**Solution**: Structured the schema to require reasoning before score for each criterion, leveraging the sequential generation nature of LLMs to produce more considered evaluations.

### Schema Description Independence
**Problem**: Schema description fields are ignored by some providers (particularly Ollama), leading to inconsistent behavior across providers and potential evaluation failures.

**Solution**: Moved all evaluation criteria descriptions into the prompt text using key-value mapping, ensuring consistent behavior across all providers regardless of their schema description support.

### Multi-Provider Comparison
**Problem**: Different LLM providers may have varying evaluation tendencies and biases, making it important to compare assessments across models.

**Solution**: Used the compat module's generate_with_schema to easily evaluate the same essay across cloud providers (Gemini, OpenAI) and local models (Ollama), revealing differences in evaluation approaches and scoring patterns between different model architectures.

### Intentionally Flawed Test Essay
**Problem**: Testing evaluation systems with well-written essays doesn't reveal whether the system can identify common writing flaws and logical fallacies.

**Solution**: Created a deliberately problematic essay with multiple issues (unsupported claims, ad hominem attacks, informal language) to verify the evaluation system's ability to detect and articulate specific weaknesses.