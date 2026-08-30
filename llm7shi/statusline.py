"""Rich-based progress display that coexists with streamed LLM output.

`ConsoleStream` (see `llm7shi.terminal`) is designed for subclassing so downstream
applications can route output through a custom UI. `StatusLine` is a ready-made
implementation built on Rich's `Progress`: pass `status_line.stream` as the `file=`
argument to a streaming call (e.g. `generate_content_retry(..., file=status_line.stream)`)
so streamed model output and a live progress bar share the same Rich `Console` and
don't clobber each other. Rate-limit retry countdowns become a temporary row within
the same live display instead of a raw `\\r` countdown.

Requires the `statusline` extra (`pip install llm7shi[statusline]`) for Rich.
This module is never imported by llm7shi/__init__.py, so `import llm7shi` alone
never pulls in Rich, which is much heavier than terminal.py's colorama dependency.
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


class MofNColumn(ProgressColumn):
    """`completed/total`, e.g. line-number / lines-in-task.

    A task may override the numerator via the `remaining` field (e.g. the retry
    countdown, where the bar fills forward but the number counts down).
    """

    # Deliberately not parameterized: at this size a variant format such as
    # `(m/n)` is better written as a fresh ProgressColumn than as a knob here.
    # Whatever replaces it should still honor `remaining`, though.
    def render(self, task) -> Text:
        n = int(task.total) if task.total is not None else "?"
        numerator = task.fields.get("remaining", task.completed)
        return Text(f"{int(numerator)}/{n}", style="progress.download")


class ElapsedColumn(ProgressColumn):
    """Elapsed time since a start timestamp the caller supplies.

    Rich's built-in elapsed column measures from when the *task* was added, which
    doesn't answer "how long has this run been going" across a batch of many tasks.
    A run may also span several processes — a Makefile launching one process per
    item, say — in which case only the caller knows when it really started, so the
    origin is a `time.time()` timestamp that can be handed across process
    boundaries rather than anything this process can measure for itself.

    Suppressed for tasks with `show_elapsed=False` (e.g. the retry countdown row),
    since it would duplicate the elapsed time already shown on the main progress line.
    """

    def __init__(self, started_at: float):
        super().__init__()
        self.started_at = started_at

    def elapsed(self) -> float:
        return time.time() - self.started_at

    def render(self, task) -> Text:
        if not task.fields.get("show_elapsed", True):
            return Text("")
        m, s = divmod(int(self.elapsed()), 60)
        h, m = divmod(m, 60)
        text = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
        return Text(text, style="progress.elapsed")


class ProcessElapsedColumn(ElapsedColumn):
    """Elapsed time since process start (not since this task was added).

    Wall-clock time is the wrong measure when nothing outside this process needs
    to agree on the origin: `time.monotonic()` can't jump backwards under an NTP
    correction. `started_at` therefore holds a monotonic reading rather than the
    unix timestamp the base class takes, which is why `elapsed()` is overridden
    to read the same clock — the two are not interchangeable.
    """

    def __init__(self):
        super().__init__(_PROCESS_START)

    def elapsed(self) -> float:
        return time.monotonic() - self.started_at


class LabelColumn(TextColumn):
    """The task label.

    A named class rather than a bare `TextColumn` so that a `columns()` override
    can locate it by type (see `ProgressContext.index_of`) instead of by list
    position, which would silently break if the default layout changed.
    """

    def __init__(self, text_format: str = "[bold cyan]{task.description}"):
        super().__init__(text_format)


class SeparatorColumn(TextColumn):
    """The `|` dividing the label from the bar; named for the same reason."""

    def __init__(self, text_format: str = "|"):
        super().__init__(text_format)


class StatusLineConsoleStream(ConsoleStream):
    # routes through the same Rich Console that owns the progress bar, so streamed
    # text and the live bar never race for the terminal and corrupt each other
    def __init__(self, console, status_line: "StatusLine"):
        super().__init__(console)
        self.status_line = status_line

    def print(self, text: str, end: str = "\n") -> None:
        # markup=False because what flows through here is model output: a `[...]` in
        # the text is data, and letting Rich parse it silently drops the bracketed
        # run (or raises MarkupError on a stray closing tag) mid-stream
        self._console.print(text, end=end, highlight=False, markup=False)

    def wait_retry(self, delay: int, message: str = "Retrying...") -> None:
        # A \r-based countdown (the base class behavior) is doubly wrong here: it would
        # collide with an active Rich Live display the same way raw streamed text does,
        # and Rich drops the \r anyway, so the countdown would concatenate rather than
        # overwrite. Draw it as a task row either way — on the live bar when there is
        # one, otherwise on a Progress lasting only as long as the countdown.
        m = re.match(r"(.+) \((\d+/\d+)\)", message)
        display_message = f"{m.group(1)} {m.group(2)}" if m else message
        progress = self.status_line.active_progress
        if progress is not None:
            self._countdown(progress, delay, display_message)
        else:
            standalone = Progress(
                SpinnerColumn(), LabelColumn(), MofNColumn(), BarColumn(), TaskProgressColumn(),
                console=self._console,
            )
            with standalone:
                self._countdown(standalone, delay, display_message)
        self.error(message)

    def _countdown(self, progress: Progress, delay: int, display_message: str) -> None:
        # `remaining`/`show_elapsed` are read by MofNColumn/ProcessElapsedColumn;
        # a replacement column that ignores them renders this row wrong
        task = progress.add_task(
            f"[red]{display_message}", total=delay, completed=0, remaining=delay, show_elapsed=False
        )
        # the countdown belongs above whatever it is interrupting
        with progress._lock:
            progress._tasks = {task: progress._tasks.pop(task), **progress._tasks}
        try:
            for i in range(delay, -1, -1):
                progress.update(task, completed=delay - i, remaining=i)
                # Sleep on 0s as well to provide a 1-second safety margin
                time.sleep(1)
        finally:
            progress.remove_task(task)

    def error(self, text: str) -> None:
        # a Text object carries the style out of band, so an error quoting model
        # output can't be re-parsed as markup the way f"[red]{text}" would be
        self._console.print(Text(str(text), style="red"))


class StatusLine:
    # subclasses swap in their own context to customize the bar; see ProgressContext.columns()
    progress_context_class: type["ProgressContext"]

    def __init__(self, console: Console | None = None):
        # taking a Console rather than building one lets a caller send the whole
        # display to stderr (`Console(stderr=True)`), widen it, or capture it
        self.console = Console() if console is None else console
        self.stream = StatusLineConsoleStream(self.console, self)
        self.active_progress = None

    def write(self, text: str) -> None:
        self.stream.write(text)

    def log(self, text: str) -> None:
        """Print a full status line that coexists with an active progress bar."""
        self.console.print(text, highlight=False)

    def progress(self, total: int, start: int = 0, label: str | None = None,
                 started_at: float | None = None) -> "ProgressContext":
        return self.progress_context_class(self, total, start, label, started_at)


class ProgressContext:
    def __init__(self, status_line: StatusLine, total: int, completed: int, label: str | None,
                 started_at: float | None = None):
        self._status_line = status_line
        self._total = total
        self._completed = completed
        self._label = label
        # a run that outlives this process (e.g. a Makefile launching one process per
        # item) passes its own start time down; see ElapsedColumn
        self._started_at = started_at
        self._task = None
        self._outer_progress = None
        self._progress = Progress(*self.columns(), console=status_line.console)

    def columns(self) -> list[ProgressColumn]:
        """The Rich columns making up the bar, in order.

        Split out from `__init__` so a subclass can insert or replace columns
        without reimplementing the rest of the context. All attributes set in
        `__init__` (`self._label`, `self._total`, ...) are available here, and
        every entry is a distinct column class so `index_of` can find it.
        """
        columns = [SpinnerColumn()]
        if self._label:
            columns.append(LabelColumn())
        if self._started_at is not None:
            columns.append(ElapsedColumn(self._started_at))
        if len(columns) > 1:  # something to divide from the bar
            columns.append(SeparatorColumn())
        return columns + [MofNColumn(), BarColumn(), TaskProgressColumn(), ProcessElapsedColumn()]

    @staticmethod
    def index_of(columns: list[ProgressColumn], column_type: type[ProgressColumn]) -> int:
        """Position of the first column of `column_type`, for insertion points.

        Lets an override say "before the separator" rather than "at index 2":

            columns.insert(self.index_of(columns, SeparatorColumn), MyColumn())
        """
        return next(i for i, column in enumerate(columns) if isinstance(column, column_type))

    def __enter__(self):
        # saved and restored rather than cleared, so an inner bar leaves an enclosing
        # one still registered — otherwise wait_retry would build a second Progress
        # for its countdown while the enclosing live display is still on screen
        self._outer_progress = self._status_line.active_progress
        self._status_line.active_progress = self._progress
        self._progress.__enter__()
        self._task = self._progress.add_task(
            self._label or "", total=self._total, completed=self._completed
        )
        return self

    def __exit__(self, *args):
        self._status_line.active_progress = self._outer_progress
        return self._progress.__exit__(*args)

    def update(self, completed: int) -> None:
        self._progress.update(self._task, completed=completed)


StatusLine.progress_context_class = ProgressContext
