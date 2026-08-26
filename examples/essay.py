"""
Automated essay evaluation via structured output. Runs the same essay through
generate_with_schema across providers to compare evaluation tendencies/biases
between model architectures. The essay in essay.txt is deliberately flawed
(unsupported claims, ad hominem, informal language) so the evaluation can be
checked for actually catching specific weaknesses, not just praising it.
"""

import json
from pathlib import Path
from llm7shi.compat import generate_with_schema

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

def generate_prompt(criteria, essay_text):
    """Generate prompt from criteria dictionary and essay text."""
    # descriptions go in the prompt, not schema `description` fields, since some providers ignore the latter
    criteria_list = "\n".join([f"- {key}: {desc}"
                              for key, desc in criteria.items()])
    
    return f"""Evaluate the following argumentative essay on each criterion using a 5-point scale:

{criteria_list}

For each criterion, first provide reasoning that considers the evaluation process, then assign a score (1-5). Also provide an overall reasoning summary.

Essay:
{essay_text}"""

# Load essay from text file
with open(Path(__file__).with_suffix(".txt")) as f:
    essay = f.read()

# Generate schema and prompt from criteria and essay
schema = generate_schema(CRITERIA)
prompt = generate_prompt(CRITERIA, essay)

def evaluate_essay(model_name):
    """Evaluate an essay using the specified model and return the evaluation results."""
    print(f"\n{'='*60}")
    print(f"Evaluating with {model_name}")
    print(f"{'='*60}")
    
    result = generate_with_schema(
        [prompt],
        schema=schema,
        model=model_name,
        show_params=False,
    )
    
    # Calculate and display individual scores
    evaluation = json.loads(result.text)
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
