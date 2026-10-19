"""
Tests for calculator_repl.py, driven by scripted input instead of a keyboard.

Output contains color codes, so checks look for text inside the output
instead of comparing whole lines.
"""

import pytest

from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.exceptions import ConfigurationError
from app.operations import OperationFactory


@pytest.fixture
def repl(monkeypatch, capsys, config):
    """
    Returns a function: repl(["add", "2", "3", "exit"]) runs a whole session
    and returns everything the program printed.
    """
    # The REPL builds its own Calculator(); swap in one that uses the temp config
    monkeypatch.setattr("app.calculator_repl.Calculator", lambda: Calculator(config))

    def _run(inputs):
        items = iter(inputs)

        def fake_input(prompt=""):
            """Stand-in for input(): returns the next scripted line."""
            try:
                value = next(items)
            except StopIteration:
                raise EOFError            # script ran out, like pressing Ctrl+D
            # An exception class in the list is raised (used to simulate Ctrl+C)
            if isinstance(value, type) and issubclass(value, BaseException):
                raise value
            return value

        monkeypatch.setattr("builtins.input", fake_input)
        calculator_repl()
        return capsys.readouterr().out
    return _run


class TestStartupAndExit:
    def test_startup_message(self, repl):
        assert "Calculator started" in repl(["exit"])

    def test_exit_says_goodbye(self, repl):
        assert "C U LATER" in repl(["exit"])

    def test_returns_zero(self, monkeypatch, config):
        monkeypatch.setattr("app.calculator_repl.Calculator", lambda: Calculator(config))
        monkeypatch.setattr("builtins.input", lambda prompt="": "exit")
        assert calculator_repl() == 0

    def test_help_lists_every_command(self, repl):
        out = repl(["help", "exit"])
        assert "Available commands" in out
        assert ", ".join(sorted(OperationFactory._operations)) in out
        for command in ("history", "clear", "undo", "redo", "save", "load", "exit"):
            assert command in out

    def test_commands_ignore_case_and_spaces(self, repl):
        assert "Result: 2" in repl(["  ADD ", "1", "1", "exit"])

    def test_unknown_command(self, repl):
        assert "Unknown command: 'bogus'" in repl(["bogus", "exit"])

