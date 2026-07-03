"""Rich-based progress display that coexists with streamed LLM output.

`ConsoleStream` (see `llm7shi.terminal`) is designed for subclassing so downstream
applications can route output through a custom UI. `StatusLine` is a ready-made
implementation built on Rich's `Progress`: pass `status_line.stream` as the `file=`
argument to a streaming call (e.g. `generate_content_retry(..., file=status_line.stream)`)
so streamed model output and a live progress bar share the same Rich `Console` and
don't clobber each other. Rate-limit retry countdowns become a temporary row within
the same live display instead of a raw `\\r` countdown.

Requires the `statusline` extra (`pip install llm7shi[statusline]`) for Rich.
"""

import re
import time

from rich.console import Console
from rich.progress import (
    Progress, ProgressColumn, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn,
)
from rich.text import Text

from .terminal import ConsoleStream

_PROCESS_START = time.monotonic()


class _MofNColumn(ProgressColumn):
    """`completed/total`, e.g. line-number / lines-in-task.

    A task may override the numerator via the `remaining` field (e.g. the retry
    countdown, where the bar fills forward but the number counts down).
    """

    def render(self, task) -> Text:
        n = int(task.total) if task.total is not None else "?"
        numerator = task.fields.get("remaining", task.completed)
        return Text(f"{int(numerator)}/{n}", style="progress.download")


class _ProcessElapsedColumn(ProgressColumn):
    """Elapsed time since process start (not since this task was added).

    Suppressed for tasks with `show_elapsed=False` (e.g. the retry countdown row),
    since it would duplicate the elapsed time already shown on the main progress line.
    """

    def render(self, task) -> Text:
        if not task.fields.get("show_elapsed", True):
            return Text("")
        elapsed = time.monotonic() - _PROCESS_START
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        text = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        return Text(text, style="progress.elapsed")


class StatusLineConsoleStream(ConsoleStream):
    def __init__(self, console, status_line: "StatusLine"):
        super().__init__(console)
        self.status_line = status_line

    def print(self, text: str, end: str = "\n") -> None:
        self._console.print(text, end=end, highlight=False)

    def wait_retry(self, delay: int, message: str = "Retrying...") -> None:
        m = re.match(r"(.+) \((\d+/\d+)\)", message)
        display_message = f"{m.group(1)} {m.group(2)}" if m else message
        width = len(str(delay))
        if self.status_line.active_progress is not None:
            progress = self.status_line.active_progress
            task = progress.add_task(
                f"[red]{display_message}", total=delay, completed=0, remaining=delay, show_elapsed=False
            )
            with progress._lock:
                progress._tasks = {task: progress._tasks.pop(task), **progress._tasks}
            try:
                for i in range(delay, -1, -1):
                    progress.update(task, completed=delay - i, remaining=i)
                    if i == 0:
                        break
                    time.sleep(1)
            finally:
                progress.remove_task(task)
            self.error(message)
        else:
            file = self._console.file
            for i in range(delay, -1, -1):
                file.write(f"\r{message} {i:>{width}}s")
                file.flush()
                if i == 0:
                    break
                time.sleep(1)
            self.print("", end="\n")

    def error(self, text: str) -> None:
        self._console.print(f"[red]{text}")


class StatusLine:
    def __init__(self):
        self.console = Console()
        self.stream = StatusLineConsoleStream(self.console, self)
        self.active_progress = None

    def write(self, text: str) -> None:
        self.stream.write(text)

    def log(self, text: str) -> None:
        """Print a full status line that coexists with an active progress bar."""
        self.console.print(text, highlight=False)

    def progress(self, total: int, start: int = 0, label: str | None = None) -> "_ProgressContext":
        return _ProgressContext(self, total, start, label)


class _ProgressContext:
    def __init__(self, status_line: StatusLine, total: int, completed: int, label: str | None):
        columns = [SpinnerColumn()]
        if label:
            columns.append(TextColumn("[bold cyan]{task.description}"))
            columns.append(TextColumn("|"))
        columns += [_MofNColumn(), BarColumn(), TaskProgressColumn(), _ProcessElapsedColumn()]

        self._status_line = status_line
        self._progress = Progress(*columns, console=status_line.console)
        self._total = total
        self._completed = completed
        self._label = label
        self._task = None

    def __enter__(self):
        self._status_line.active_progress = self._progress
        self._progress.__enter__()
        self._task = self._progress.add_task(
            self._label or "", total=self._total, completed=self._completed
        )
        return self

    def __exit__(self, *args):
        self._status_line.active_progress = None
        return self._progress.__exit__(*args)

    def update(self, completed: int) -> None:
        self._progress.update(self._task, completed=completed)
