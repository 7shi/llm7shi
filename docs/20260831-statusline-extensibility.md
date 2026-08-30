# Making StatusLine Extensible

Date: 2026-08-31

## Background

`llm7shi.statusline` was promoted from dante-corpus in 0.14.0. Two downstream
projects then needed progress bars the default layout doesn't produce, and
neither could express that against the module as it stood:

- **dante-corpus** wanted an extra elapsed-time column right after the label,
  measuring from a start time exported by a Makefile that launches one process
  per canto. It subclassed `_ProgressContext` and imported the private
  `_MofNColumn` / `_ProcessElapsedColumn` to reuse their formatting, but still
  had to copy `__init__` wholesale.
- **multilingual-reader (trtools)** wanted a different `(m/n)` format and
  placement plus a per-task elapsed clock. It gave up on reuse entirely and
  reimplemented the context, closures and all.

The root cause was structural: `_ProgressContext.__init__` built the column list
inline and immediately constructed `Progress(*columns, ...)`, so "which columns"
had no override point, and the reusable pieces were private.

## Subclassing as the Extension Surface

The original proposal was to make the variable parts injectable through keyword
arguments on `progress()` — `label_extra` for columns to insert after the label,
`elapsed_column_factory` to swap the trailing clock. This was rejected: those two
knobs fit exactly the two known call sites, and a third caller wanting a column
somewhere else would grow a third knob. A single override point covers arbitrary
layouts instead:

```python
class MyContext(ProgressContext):
    def columns(self):
        columns = super().columns()
        columns.insert(self.index_of(columns, SeparatorColumn), MyColumn())
        return columns

class MyStatusLine(StatusLine):
    progress_context_class = MyContext
```

`progress_context_class` exists because `progress()` previously named its context
class directly, so a `StatusLine` subclass had to reimplement `progress()` just to
return a different context.

Insertion points are expressed by column *type*, not by list index. That is why
the plain `TextColumn`s became `LabelColumn` and `SeparatorColumn`: with every
entry in the default list a distinct class, `index_of()` can find one, and a
later change to the default layout carries a subclass's column along with it
instead of silently misplacing it.

## Where Customization Hooks Stop

The same treatment was tried on `MofNColumn` — a `text_format` class attribute so
that trtools' `(m/n)` variant could inherit `render()`. It was reverted. At four
lines, a column whose display differs outright is better written fresh from
`ProgressColumn` than parameterized upstream, and the attribute was mechanism
added to a class too small to justify it.

What that attempt was really protecting is the task-field protocol, which is
invisible from the column API: `wait_retry` adds its countdown row with
`remaining` (the numerator counts down while the bar fills forward) and
`show_elapsed=False` (elapsed already appears on the main line). A hand-written
column that ignores these renders the countdown wrong — which trtools' copy in
fact did. So the protocol is documented at both ends and at `add_task`, and the
knob stayed out.

`ProcessElapsedColumn` went the other way and kept a split-out `elapsed()`,
because a rewrite there loses the shared time format *and* the `show_elapsed`
suppression. The line is decomposition versus knob, not one rule for all columns.

## Two Clocks, Not One

`ElapsedColumn(started_at)` was factored out as the base, with
`ProcessElapsedColumn` deriving from it. An intermediate version had the derived
class simply pass its own construction time, dropping the module-level
`_PROCESS_START` — but that silently changed the origin for a script opening
several bars in sequence, and forced wall-clock time on a measurement that
nothing outside the process needs to agree on.

The two therefore keep different clocks: `started_at` is a `time.time()` value
precisely because it crosses process boundaries, while `ProcessElapsedColumn`
overrides `elapsed()` to read `time.monotonic()`, which cannot jump backwards
under an NTP correction. They share `render()` and nothing else; the docstrings
say the two are not interchangeable.

## A Keyword Argument After All

`StatusLine.progress()` did gain `started_at`, which sits oddly beside the
rejection of `label_extra`. The distinction is that `started_at` is a value the
run *has*, not a knob on the layout: only the caller can know when a run spanning
several processes began, and there is no other way to express it, while where its
column lands stays the module's decision. With it, dante-corpus needs no
`ProgressContext` subclass and no column of its own at all — one step past what
the original proposal was aiming for. trtools still overrides `columns()`, since
its differences are structural rather than a single missing value.

By the same test, counters for retries and accumulated backoff were *not* added:
`wait_retry` already receives both the message (carrying `{retry}/{max_retries}`
from a caller-supplied template) and `delay`, so a library-side counter would
only re-hold values the application has in hand.

## Defects Found on the Way

Reading the downstream workarounds surfaced three bugs that were not extensibility
problems at all:

- **Rich markup in streamed output.** `print()` left `markup=True`, so model text
  containing `[obl:a=(126,3)]` lost the bracketed run and a stray `[/b]` raised
  `MarkupError` mid-stream. `error()` had the same flaw through `f"[red]{text}"`.
  dante-corpus was subclassing `StatusLineConsoleStream` purely to work around
  this.
- **Retry countdown with no active bar.** The `\r` fallback inherited from
  `ConsoleStream` is meaningless through a Rich console, which drops the `\r` and
  concatenates: `Retrying... 3sRetrying... 2s...`. The countdown now builds a
  short-lived bar of its own.
- **Nested bars.** `__exit__` cleared `active_progress` unconditionally, so
  leaving an inner bar deregistered an enclosing one that was still live. It now
  saves and restores.

## Compatibility

Dropping the underscore from `_MofNColumn`, `_ProcessElapsedColumn` and
`_ProgressContext` breaks any code importing the private names. No aliases were
added, since preserving them would preserve the very practice the rename exists
to end; dante-corpus is the only known importer. Its `except ImportError` guard
makes the break silent — it degrades to plain stderr output rather than raising —
so the downstream fix has to land before the release. multilingual-reader imports
only `StatusLine` and is unaffected by the rename, though it does inherit the
markup change.

## Deferred: One Progress Instead of One Per Bar

Because Rich fixes a `Progress`'s columns at construction and the layout depends
on per-bar arguments, `ProgressContext` rebuilds both per `with` block. The
alternative — one long-lived `Progress` on the `StatusLine` with `progress()`
merely adding a task, and the varying parts moved into task fields the way
`remaining` and `show_elapsed` already are — would collapse the three extension
points into one and make nesting natural.

It was deferred rather than adopted: bars would all share one column layout,
which is exactly what trtools varies per bar, and the change is far wider than
the rename it would ride along with. The construction cost that might otherwise
motivate it is not a factor, since `progress()` is called once per bar, not per
`update()`.
