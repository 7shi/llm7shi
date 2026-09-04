"""
Automated essay evaluation via structured output. Runs the same essay through a
Client across providers to compare evaluation tendencies/biases between model
architectures. The essay in essay.txt is deliberately flawed
(unsupported claims, ad hominem, informal language) so the evaluation can be
checked for actually catching specific weaknesses, not just praising it.
"""

import argparse
from pathlib import Path
from pydantic import Field, create_model
from llm7shi import Client, create_json_descriptions_prompt
from args import parse_model_args

# single source of truth: the schema and its field descriptions are both derived from this dict, so criteria stay in sync
CRITERIA = {
    "clarity_of_argument": "How clear and well-defined is the main argument?",
    "supporting_evidence": "How well is the argument supported with facts and examples?",
    "logical_structure": "How well organized and logically flowing is the essay?",
    "persuasiveness": "How convincing is the argument?",
    "writing_quality": "How well-written is the essay in terms of grammar, style, and vocabulary?"
}

def generate_schema(criteria):
    """Dynamically build a Pydantic model from the criteria dictionary."""
    fields = {}
    for key in criteria:
        # a per-criterion model, named after the key, nesting reasoning before score
        # so the model reasons before judging, not after
        criterion_model = create_model(
            "".join(word.capitalize() for word in key.split("_")) + "Criterion",
            reasoning=(str, ...),  # (type, ...): required field, no default value
            score=(int, Field(..., ge=1, le=5)),
        )
        # description carries the criterion's meaning on the field itself, so
        # create_json_descriptions_prompt() can turn it into a prompt message
        # for providers (e.g. Ollama) that ignore schema `description` fields
        fields[key] = (criterion_model, Field(..., description=criteria[key]))

    fields["overall_reasoning"] = (str, ...)  # required field, no default value

    return create_model("EssayEvaluation", **fields)

# Generate the schema criteria descriptions are derived from
schema = generate_schema(CRITERIA)

# Load essay from text file
with open(Path(__file__).with_suffix(".txt")) as f:
    essay = f.read()

# "above": the essay is sent as the message before this one, so it precedes this prompt
PROMPT = """Evaluate the argumentative essay above on each criterion using a 5-point scale.

For each criterion, first provide reasoning that considers the evaluation process, then assign a score (1-5). Also provide an overall reasoning summary."""

# Ollama ignores schema `description` fields; send them as a separate message so they aren't dropped
json_descriptions = create_json_descriptions_prompt(schema)

def evaluate_essay(model_name):
    """Evaluate an essay using the specified model and return the evaluation results."""
    print(f"\n{'='*60}")
    print(f"Evaluating with {model_name}")
    print(f"{'='*60}")
    
    # keep_history=False: a single evaluation, so nothing should be carried
    # over -- each model is compared on the same blank history
    client = Client(model=model_name, show_params=False, keep_history=False)
    
    # the essay is material to evaluate, not an instruction about how to behave,
    # so it's sent as its own user message rather than the system prompt
    result = client(["Essay:\n" + essay, PROMPT, json_descriptions], schema)

    # Calculate and display individual scores
    # Client parses the JSON while validating it for the retry loop, so
    # result.data is already a validated EssayEvaluation instance
    evaluation = result.data
    scores = []
    print("\nDetailed Scores:")
    for key, desc in CRITERIA.items():
        score = getattr(evaluation, key).score
        scores.append(score)
        print(f"- {key.replace('_', ' ').title()}: {score}/5")
    
    avg_score = sum(scores) / len(scores)
    print(f"\nOverall Score: {avg_score:.2f}/5")

# Display the essay to be evaluated
print("Essay to be evaluated:")
print("=" * 60)
print(essay)
print("=" * 60)

args = parse_model_args(argparse.ArgumentParser(description=__doc__))
evaluate_essay(args.model)
