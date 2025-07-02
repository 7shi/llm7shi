import json
from pathlib import Path
from llm7shi.compat import generate_with_schema, VENDOR_PREFIXES

# Define evaluation criteria and their descriptions
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
                "reasoning": {"type": "string"},
                "score": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["reasoning", "score"]
        }
    
    properties["overall_reasoning"] = {
        "type": "string",
        "description": "Summary of the overall evaluation"
    }
    
    return {
        "type": "object",
        "properties": properties,
        "required": list(criteria.keys()) + ["overall_reasoning"]
    }

def generate_prompt(criteria, essay_text):
    """Generate prompt from criteria dictionary and essay text."""
    criteria_list = "\n".join([f"- {key}: {desc}" 
                              for key, desc in criteria.items()])
    
    return f"""Evaluate the following argumentative essay on each criterion using a 5-point scale:

{criteria_list}

For each criterion, provide a score (1-5) and reasoning. Also provide an overall reasoning summary.

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

# Evaluate with all models
for model in VENDOR_PREFIXES:
    evaluate_essay(model)
