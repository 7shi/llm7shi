"""
Automated essay evaluation via structured output. Runs the same essay through a
Client across providers to compare evaluation tendencies/biases between model
architectures. The essay in essay.txt is deliberately flawed
(unsupported claims, ad hominem, informal language) so the evaluation can be
checked for actually catching specific weaknesses, not just praising it.
"""

from pathlib import Path
from llm7shi import Client

# single source of truth: schema and prompt are both derived from this dict, so criteria stay in sync
CRITERIA = {
    "clarity_of_argument": "How clear and well-defined is the main argument?",
    "supporting_evidence": "How well is the argument supported with facts and examples?",
    "logical_structure": "How well organized and logically flowing is the essay?",
    "persuasiveness": "How convincing is the argument?",
    "writing_quality": "How well-written is the essay in terms of grammar, style, and vocabulary?"
}

def generate_schema(criteria):
    """Generate JSON schema from criteria dictionary."""
    properties = {}
    for key in criteria:
        properties[key] = {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},  # ordered before score so the model reasons before judging, not after
                "score": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["reasoning", "score"]
        }
    
    properties["overall_reasoning"] = {"type": "string"}
    
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys())
    }

def generate_prompt(criteria):
    """Generate prompt from criteria dictionary."""
    # descriptions go in the prompt, not schema `description` fields, since some providers ignore the latter
    criteria_list = "\n".join([f"- {key}: {desc}"
                              for key, desc in criteria.items()])
    
    # "above": the essay is a prior turn in the history, so it precedes this prompt
    return f"""Evaluate the argumentative essay above on each criterion using a 5-point scale:

{criteria_list}

For each criterion, first provide reasoning that considers the evaluation process, then assign a score (1-5). Also provide an overall reasoning summary."""

# Load essay from text file
with open(Path(__file__).with_suffix(".txt")) as f:
    essay = f.read()

# Generate schema and prompt from criteria and essay
schema = generate_schema(CRITERIA)
prompt = generate_prompt(CRITERIA)

def evaluate_essay(model_name):
    """Evaluate an essay using the specified model and return the evaluation results."""
    print(f"\n{'='*60}")
    print(f"Evaluating with {model_name}")
    print(f"{'='*60}")
    
    # a fresh Client per model: each evaluation must start from the same blank
    # history so the models are compared on equal footing
    client = Client(model=model_name, show_params=False)
    # the essay is material to evaluate, not an instruction about how to behave,
    # so it goes into the history as a prior turn rather than the system prompt
    client.history.append({"role": "user", "content": "Essay:\n" + essay})
    result = client(prompt=prompt, schema=schema)
    
    # Calculate and display individual scores
    # Client parses the JSON while validating it for the retry loop, so
    # result.data is already the decoded dict
    evaluation = result.data
    scores = []
    print("\nDetailed Scores:")
    for key, desc in CRITERIA.items():
        score = evaluation[key]["score"]
        scores.append(score)
        print(f"- {key.replace('_', ' ').title()}: {score}/5")
    
    avg_score = sum(scores) / len(scores)
    print(f"\nOverall Score: {avg_score:.2f}/5")

# Display the essay to be evaluated
print("Essay to be evaluated:")
print("=" * 60)
print(essay)
print("=" * 60)

evaluate_essay("ollama:")
