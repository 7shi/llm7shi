"""Shared CLI arg parsing for examples: adds -m/--model to a caller-supplied
parser rather than owning parser construction, so each example stays free to
add its own arguments before parsing.
"""

def parse_model_args(parser, default_model="ollama:"):
    """Add -m/--model and --completion to parser and return the parsed args.

    --completion forces llm7shi.openai.USE_COMPLETION, so real OpenAI (no custom
    base_url) falls back to Chat Completions instead of the Responses API
    (see llm7shi/openai.py).
    """
    parser.add_argument(
        "-m", "--model",
        default=default_model,
        help="Model name with optional vendor prefix (e.g. openai:gpt-4.1-mini)",
    )
    parser.add_argument(
        "--completion", action="store_true",
        help="Force Chat Completions instead of the Responses API for real OpenAI",
    )
    args = parser.parse_args()

    if args.completion:
        import llm7shi.openai
        llm7shi.openai.USE_COMPLETION = True

    return args
