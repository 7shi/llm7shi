import io
import re

import pytest

from llm7shi.monitor import StreamProcessor


def _strip_ansi(text):
    """Remove ANSI escape sequences so display assertions are readable."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _run(thought_chunks=(), text_chunks=()):
    """Drive a StreamProcessor and return (processor, ansi-stripped display)."""
    buf = io.StringIO()
    processor = StreamProcessor(file=buf)
    for chunk in thought_chunks:
        processor.add_thought(chunk)
    for chunk in text_chunks:
        processor.add_text(chunk)
    processor.finalize()
    return processor, _strip_ansi(buf.getvalue())


def test_headers_shown_once():
    """Thinking and answer headers each appear exactly once on transition.

    The ANSI-stripped display has the markdown bold markers converted away, so
    the visible header text is "Thinking..." / "Answer:" without asterisks.
    """
    _, display = _run(["a", "b"], ["c", "d"])
    assert display.count("🤔 Thinking...") == 1
    assert display.count("💡 Answer:") == 1


def test_answer_only_has_no_headers():
    """Pure answer output (no thoughts) shows neither header."""
    _, display = _run([], ["just the answer"])
    assert "🤔" not in display
    assert "💡" not in display
    assert display == "just the answer\n"


def test_thoughts_only_has_thinking_header():
    """Thoughts without an answer show the thinking header but no answer header."""
    _, display = _run(["thinking"], [])
    assert "🤔 Thinking..." in display
    assert "💡" not in display


@pytest.mark.parametrize("thought_tail", ["", "\n", "\n\n", "\n\n\n\n"])
def test_exactly_one_blank_line_between_sections(thought_tail):
    """Regardless of trailing newlines in thoughts, sections are split by one blank line."""
    _, display = _run(["reason" + thought_tail], ["answer"])
    # Find the boundary: thinking content followed by the answer header.
    match = re.search(r"reason(\n*)💡 Answer:", display)
    assert match is not None, display
    # "reason\n\n💡" -> exactly two newlines == one blank line between them.
    assert match.group(1) == "\n\n", repr(display)


def test_internal_blank_lines_preserved_and_trimmed_at_end():
    """Blank lines inside content survive; trailing blank lines are trimmed to one newline."""
    _, display = _run([], ["para1\n\npara2\n\n\n"])
    assert "para1\n\npara2" in display
    assert display.endswith("\n")
    assert not display.endswith("\n\n")


def test_raw_text_preserved_verbatim():
    """Accumulated thoughts/text must equal the raw chunk concatenation (KV-cache safety)."""
    thought_chunks = ["Let me ", "think...\n\n\n"]
    text_chunks = ["The ", "answer\n\n"]
    processor, _ = _run(thought_chunks, text_chunks)
    assert processor.thoughts == "".join(thought_chunks)
    assert processor.text == "".join(text_chunks)


def test_empty_output_ends_with_single_newline():
    """Empty output still terminates with a newline, matching the providers' behavior."""
    _, display = _run([], [])
    assert display == "\n"


def test_max_length_detected_and_reported():
    """max_length on the answer stops generation and is reported."""
    buf = io.StringIO()
    processor = StreamProcessor(file=buf, max_length=5)
    assert processor.add_text("123456789") is False
    assert processor.max_length_exceeded == 5


def test_repetition_flag_aggregated_across_sections():
    """repetition_detected reflects either the thoughts or answer monitor."""
    buf = io.StringIO()
    processor = StreamProcessor(file=buf)
    # A long run of newlines trips the weighted-whitespace detector in the thoughts.
    assert processor.add_thought("\n" * 600) is False
    assert processor.repetition_detected is True


def test_file_none_accumulates_without_error():
    """With file=None, no display occurs but text is still accumulated."""
    processor = StreamProcessor(file=None)
    assert processor.add_thought("thought") is True
    assert processor.add_text("answer") is True
    processor.finalize()
    assert processor.thoughts == "thought"
    assert processor.text == "answer"
