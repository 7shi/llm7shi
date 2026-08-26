# Inlining Module Documentation into Code Comments

This document describes the 2026-08-26 restructuring of the module `.md` documentation
policy: moving single-anchor rationale out of paired `.md` files and into code comments,
and narrowing where the paired `.md` tier applies at all.

## Background

`DOCUMENTATION.md` establishes a two-tier structure: each `module.py` has a paired
`module.md` holding implementation rationale ("why"), while the code itself stays free of
that explanation ("how" only). This works well when a design decision spans multiple
functions or files — there's no single place in the code to anchor the explanation, so a
separate document is the only option.

## Problem: Split Attention on Single-Anchor Rationale

In practice, many `.md` entries were "Problem/Solution" pairs that referred to exactly one
function, line, or constant. For example, `xml.md` explained the CDATA-escaping trick in
`escape_cdata_content()` and the `indent=""` choice in `xml_to_str()` — each tied to a
single, specific spot in `xml.py`. Reading or editing that code meant jumping to a second
file to recover the reasoning, and editing the code without touching the doc risked letting
the two drift apart. The doc wasn't doing anything a comment couldn't do more cheaply.

## Solution: Inline Rationale at the Anchor Point

`DOCUMENTATION.md` now distinguishes by whether rationale can be localized:

- Rationale anchored to one function/line/constant → a short WHY comment at that spot,
  removed from the `.md`.
- Rationale that spans multiple functions/files, describes cross-cutting architecture, or
  compares alternatives at the module level → stays in the `.md`, since there's no single
  line to attach it to.

Applying this across `llm7shi/` moved roughly 100 Problem/Solution items into terse code
comments (e.g. the CDATA/`indent=""` examples above), while genuinely cross-cutting
rationale — such as `compat.md`'s multi-provider schema-format differences, or `stream.md`'s
Template Method Pattern rationale spanning the whole module — was left in place.

## Extending the Policy: Dropping Paired `.md` for `tests/` and `examples/`

The first pass only localized single-anchor rationale within each module's existing `.md`.
A follow-up question was whether the paired-`.md` tier should exist at all for `tests/` and
`examples/`: those files are small, single-purpose, standalone scripts, unlike `llm7shi/`
modules that interact with each other and can carry genuine cross-module rationale. For a
file that small, a second file adds overhead without buying anything a docstring can't.

The policy was narrowed accordingly: paired `.md` files now apply only to `llm7shi/`.
For `tests/` and `examples/`, all remaining rationale — including content that previously
would have stayed in the `.md` as "spanning the whole file" — was folded into a top-of-file
module docstring in the `.py`. Rationale genuinely shared across multiple files (e.g. a
testing pattern reused by several test modules, or a design reused across several example
scripts) became a short "See also: other_file.py" note in the docstring rather than a
justification for inventing a new shared document.

## Migration Process

The migration ran in two rounds, each split into parallel passes over non-overlapping
directories to avoid concurrent edits to the same files:

1. Localize single-anchor rationale into code comments, across `llm7shi/`, `tests/`, and
   `examples/` in parallel.
2. Drop the paired `.md` tier for `tests/` and `examples/`: fold their remaining `.md`
   content into docstrings, then delete the 26 now-empty `.md` files (11 in `examples/`, 15
   in `tests/`).

Both rounds were verified with `uv run pytest -q` (249 tests) after each pass, since the
migration was comment/docstring-only and should never change behavior.

## Follow-up: Dead Links in Directory READMEs

Deleting the per-file `.md` docs broke inbound links: `examples/README.md` and
`tests/README.md` each had a `**Documentation**: [file.md](file.md)` line per example/test
entry, pointing at files that no longer existed. These were removed in a follow-up pass.
The lesson: removing a paired `.md` requires checking for inbound links from directory
`README.md` files, which aren't part of the `module.py`/`module.md` pairing itself.

## Scope and Caveats

The paired `.md` tier now applies only to the 14 modules under `llm7shi/`. `tests/` and
`examples/` carry no `.md` files besides their directory `README.md`. See
[DOCUMENTATION.md](../DOCUMENTATION.md) for the current policy text, including the
localization rule and the reduced "What to Include/Exclude" lists for `llm7shi/` `.md`
files.
