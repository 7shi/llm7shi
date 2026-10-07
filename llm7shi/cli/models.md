# cli/models.py - `llm7shi models` Command

## Why This Implementation Exists

### One `models` Command With Providers Below It
**Problem**: Listing models is the only OpenRouter-specific task the CLI has;
a per-provider command (`llm7shi openrouter models`) would add a top-level
name holding a single subcommand.

**Solution**: Group by task instead: `llm7shi models <provider>`. Each provider
gets its own subparser, since listing options such as `--free` only make sense
for one provider.

### OpenRouter First
**Problem**: The `openrouter:` prefix accepts several hundred model IDs, and the
free tier (`:free` suffix) changes often. Picking one meant opening the website
or running ad-hoc `curl | jq` pipelines, neither of which showed how a model
would behave when called through llm7shi.

**Solution**: Fetch the list live on every run and print it sorted by ID, with
`--free` keeping only the free variants.

### Choosing Columns for llm7shi Callers
**Problem**: Each model record has around twenty fields; printing them all is
unreadable, while printing only IDs hides differences that change how a call
behaves.

**Solution**: Show only fields that decide whether llm7shi's own options work
with a model (reasoning control, structured output, tools) plus the practical
limits for choosing one (context, output length, price, input types, expiration).
Descriptions, tokenizer, benchmarks, and the detailed pricing breakdown are left
out to keep one model per line.
