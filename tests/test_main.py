"""
Tests for the command-line entry point in __main__.py.
"""

import pytest

from llm7shi import __version__
from llm7shi.__main__ import main


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out == f"llm7shi {__version__}\n"


def test_usage_help_shows_invoked_name(capsys):
    # "usage" is dispatched before the top-level parser, so its help must still
    # name the command as typed rather than a bare script name
    with pytest.raises(SystemExit):
        main(["usage", "-h"])
    assert capsys.readouterr().out.startswith("usage: llm7shi usage ")
