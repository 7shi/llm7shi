from io import StringIO
from unittest.mock import patch

from rich.console import Console

from llm7shi.statusline import StatusLine, StatusLineConsoleStream


def make_status_line() -> StatusLine:
    # Real Console with a StringIO target keeps assertions off TTY detection/ANSI styling
    # while still exercising genuine Rich rendering rather than a mock
    status_line = StatusLine()
    status_line.console = Console(file=StringIO(), force_terminal=False, width=80)
    status_line.stream = StatusLineConsoleStream(status_line.console, status_line)
    return status_line


class TestStatusLineConsoleStream:
    def test_print(self):
        status_line = make_status_line()
        status_line.stream.print("hello")
        assert "hello" in status_line.console.file.getvalue()

    def test_error(self):
        status_line = make_status_line()
        status_line.stream.error("boom")
        assert "boom" in status_line.console.file.getvalue()

    def test_wait_retry_without_active_progress(self):
        # Plain fallback countdown path (no Progress active)
        status_line = make_status_line()
        with patch("time.sleep") as mock_sleep:
            status_line.stream.wait_retry(2, message="Retrying (1/4)...")
            assert mock_sleep.call_count == 3
        output = status_line.console.file.getvalue()
        assert "Retrying (1/4)... 2s" in output
        assert "Retrying (1/4)... 0s" in output

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
