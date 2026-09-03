"""
The tqdm-equivalent use of llm7shi.statusline: a single progress bar over a
batch of generations, with no subclassing or custom columns. Answers are plain
text rather than structured output, so the model's tokens stream to the terminal
while the bar is live -- the situation StatusLine exists to handle, and the
reason a plain tqdm would not do here.

The essay in essay.txt is deliberately flawed, so the five questions have
something to find. See also: essay.py, which scores the same essay with a schema.

Requires the statusline extra: uv sync --extra statusline
"""

import argparse
from pathlib import Path
from llm7shi import Client
from llm7shi.statusline import StatusLine
from args import parse_model_args

args = parse_model_args(argparse.ArgumentParser(description=__doc__))

QUESTIONS = [
    "Summarize the main argument in two sentences.",
    "List the claims that are made without supporting evidence.",
    "Identify the logical fallacies, naming each one.",
    "How does the essay treat opposing viewpoints?",
    "Suggest three concrete revisions that would strengthen it.",
]

essay = Path(__file__).with_name("essay.txt").read_text()

ui = StatusLine()

# the bar counts questions, so it advances once per generation rather than per token
with ui.progress(len(QUESTIONS), label="essay") as prog:
    for i, question in enumerate(QUESTIONS, 1):
        # ui.log() instead of print(): a bare print would be overwritten by the
        # live bar redrawing itself
        ui.log(f"\n[bold]Q{i}.[/bold] {question}\n")
        # a fresh Client per question rather than one reused across the loop: the
        # questions are independent, and carrying history would let each answer
        # steer the next
        client = Client(
            model=args.model,
            # routes the stream through the console that owns the bar; with the
            # default sys.stdout the two would interleave and corrupt each other
            file=ui.stream,
            show_params=False,
        )
        # the essay is material to ask about, not an instruction about how to
        # behave, so it's sent as its own user message rather than the system prompt
        client(["Essay:\n" + essay, question])
        prog.update(i)
