# cli/chat.py - `llm7shi chat` Command

## Why This Implementation Exists

Trying a model meant writing a throwaway script per model, and comparing how
fast or how verbosely models answer meant reading usage out of each script's
output by hand.

### Built on `Client`
**Problem**: An interactive session needs conversation history, quality
retries, streaming output, and thinking control, all of which a direct
`generate_with_schema()` loop would have to reimplement.

**Solution**: Drive one `Client` for the whole session. It already keeps
history, retries, and streams to its `file`, so the command only reads input,
handles `/` commands, and toggles `Client.include_thoughts` for `/think`.

### Stats per Turn Instead of `Client.show_usage`
**Problem**: `show_usage` prints each attempt's raw `Usage` repr, which is noisy
in a chat and has no speed figure, the number most useful when comparing models.

**Solution**: Print one compact `input:N (N tps) | output:N (N tps) | ...` line per turn,
summing every attempt the turn made. The speeds come from the `Response` stream
timestamps (see `response.md`) rather than from timing the terminal output, so
retry countdowns and markdown buffering stay out of them. The output speed
counts the answer alone: OpenAI and Gemini don't stream their thinking in full,
so timing reasoning tokens would only add noise.
