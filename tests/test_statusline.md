# test_statusline.py - Progress Display Tests

## Why These Tests Exist

### Headless Rich Output Verification
**Problem**: `StatusLine` owns a real Rich `Console` writing to the real terminal by default, which is unsuitable for automated tests and would make assertions depend on TTY detection and ANSI styling.

**Solution**: Tests construct a `StatusLine` and then replace its `console`/`stream` with a `Console(file=StringIO(), force_terminal=False)`, so output can be asserted as plain text while still exercising the real Rich rendering path (not a mock).

### Retry Countdown With and Without an Active Progress Bar
**Problem**: `StatusLineConsoleStream.wait_retry` has two code paths — a temporary progress-bar row when a `Progress` is active, and a plain fallback countdown otherwise — and only the active-progress path touches Rich's private `progress._lock`/`_tasks` reordering.

**Solution**: Both paths are tested directly, patching `time.sleep` to avoid real delays. The active-progress case is exercised inside a real `status_line.progress()` context so the temporary task add/reorder/remove sequence runs against genuine `Progress` internals rather than a mock.

### `active_progress` Lifecycle
**Problem**: `wait_retry` and other code decide their behavior based on `status_line.active_progress`, which must be set on entering a progress context and cleared on exit (including on exceptions) for nested or sequential progress bars to behave correctly.

**Solution**: A test asserts `active_progress` is `None` before and after the `with status_line.progress(...)` block, and non-`None` inside it.
