"""Tests for StatusLine progress display."""

import time
import re
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from rich.console import Console
from rich.progress import TextColumn

from llm7shi.statusline import (
    ElapsedColumn, MofNColumn, ProcessElapsedColumn, ProgressContext, SeparatorColumn,
    StatusLine,
)


def make_status_line(cls: type[StatusLine] = StatusLine) -> StatusLine:
    # Real Console with a StringIO target keeps assertions off TTY detection/ANSI styling
    # while still exercising genuine Rich rendering rather than a mock
    return cls(Console(file=StringIO(), force_terminal=False, width=80))


class TestStatusLineConsoleStream:
    def test_print(self):
        status_line = make_status_line()
        status_line.stream.print("hello")
        assert "hello" in status_line.console.file.getvalue()

    def test_print_does_not_parse_markup(self):
        # model output is data: a bracketed run must survive verbatim
        status_line = make_status_line()
        status_line.write("citation [obl:a=(126,3)] here\n")
        assert "[obl:a=(126,3)]" in status_line.console.file.getvalue()

    def test_error_does_not_parse_markup(self):
        status_line = make_status_line()
        status_line.stream.error("failed on [/b] fragment")  # would raise MarkupError
        assert "[/b]" in status_line.console.file.getvalue()

    def test_error(self):
        status_line = make_status_line()
        status_line.stream.error("boom")
        assert "boom" in status_line.console.file.getvalue()

    def test_wait_retry_without_active_progress(self):
        # No bar to attach to, so the countdown gets one of its own
        status_line = StatusLine(Console(file=StringIO(), force_terminal=True, width=60))
        with patch("time.sleep") as mock_sleep:
            status_line.stream.wait_retry(2, message="Retrying (1/4)...")
            assert mock_sleep.call_count == 3
        output = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", status_line.console.file.getvalue())
        assert "Retrying 1/4 2/2" in output  # the countdown row, numerator counting down
        assert "Retrying (1/4)..." in output  # and the message left behind afterwards
        assert status_line.active_progress is None

    def test_wait_retry_with_active_progress(self):
        status_line = make_status_line()
        # Runs inside a real progress() context so the temporary task add/reorder/remove
        # sequence exercises Rich's private progress._lock/_tasks, not a mock
        with status_line.progress(total=10, label="task") as ctx:
            with patch("time.sleep") as mock_sleep:
                status_line.stream.wait_retry(2, message="Retrying (1/4)...")
                assert mock_sleep.call_count == 3
        output = status_line.console.file.getvalue()
        assert "Retrying (1/4)..." in output


class TestStatusLine:
    def test_write_delegates_to_stream(self):
        status_line = make_status_line()
        status_line.write("hello\n")
        assert "hello" in status_line.console.file.getvalue()

    def test_log(self):
        status_line = make_status_line()
        status_line.log("status")
        assert "status" in status_line.console.file.getvalue()

    def test_progress_context_updates_and_resets_active_progress(self):
        status_line = make_status_line()
        # active_progress gates wait_retry's behavior, so it must be set/cleared correctly
        # even across nested or sequential progress bars
        assert status_line.active_progress is None
        with status_line.progress(total=5, label="items") as ctx:
            assert status_line.active_progress is not None
            ctx.update(3)
        assert status_line.active_progress is None
        output = status_line.console.file.getvalue()
        assert "items" in output


class TestSubclassCustomization:
    def test_columns_override_adds_extra_column(self):
        # The extension point downstream projects use: add a column without
        # reimplementing __init__ or importing private names
        class MyContext(ProgressContext):
            def columns(self):
                columns = super().columns()
                # located by column type, not by list position
                columns.insert(self.index_of(columns, SeparatorColumn), TextColumn("EXTRA"))
                return columns

        class MyStatusLine(StatusLine):
            progress_context_class = MyContext

        status_line = make_status_line(MyStatusLine)
        with status_line.progress(total=5, label="items") as ctx:
            assert isinstance(ctx, MyContext)
            ctx.update(1)
        assert "EXTRA" in status_line.console.file.getvalue()

    def test_default_context_class_is_progress_context(self):
        assert StatusLine.progress_context_class is ProgressContext

    def test_mofn_remaining_field_drives_numerator(self):
        # The implicit protocol a custom m/n column has to reproduce: wait_retry's
        # countdown row fills the bar forward while the number counts down
        task = SimpleNamespace(total=10, completed=3, fields={"remaining": 7})
        assert MofNColumn().render(task).plain == "7/10"

    def test_elapsed_column_from_supplied_start(self):
        column = ElapsedColumn(time.time() - 3725)
        assert column.render(SimpleNamespace(fields={})).plain == "1:02:05"
        # under an hour the hours part is dropped
        assert ElapsedColumn(time.time() - 65).render(SimpleNamespace(fields={})).plain == "1:05"
        # and the retry countdown row suppresses it entirely
        assert column.render(SimpleNamespace(fields={"show_elapsed": False})).plain == ""

    def test_process_elapsed_column_measures_from_process_start(self):
        # monotonic origin, so it is unaffected by wall-clock adjustments
        column = ProcessElapsedColumn()
        assert column.started_at <= time.monotonic()
        assert column.render(SimpleNamespace(fields={})).plain == "0:00"

    def test_started_at_adds_elapsed_column_after_the_label(self):
        # dante-corpus' case, with no subclassing at all
        status_line = make_status_line()
        with status_line.progress(total=5, label="canto", started_at=time.time() - 3725) as ctx:
            ctx.update(1)
        line = [l for l in status_line.console.file.getvalue().splitlines() if l.strip()][-1]
        assert "canto 1:02:05 |" in line

    def test_started_at_without_label_still_gets_a_separator(self):
        status_line = make_status_line()
        with status_line.progress(total=5, started_at=time.time() - 65) as ctx:
            ctx.update(1)
        line = [l for l in status_line.console.file.getvalue().splitlines() if l.strip()][-1]
        assert "1:05 |" in line

    def test_nested_progress_restores_the_enclosing_bar(self):
        status_line = make_status_line()
        with status_line.progress(total=3, label="outer") as outer:
            with status_line.progress(total=3, label="inner"):
                assert status_line.active_progress is not None
            # the enclosing bar is still live, so wait_retry must still use a task row
            assert status_line.active_progress is outer._progress
        assert status_line.active_progress is None
