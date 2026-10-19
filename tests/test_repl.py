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


class TestOperationCommands:
    @pytest.mark.parametrize("command, a, b, expected", [
        ("add", "2", "3", "Result: 5"),
        ("subtract", "2", "3", "Result: -1"),
        ("multiply", "4", "2.5", "Result: 10"),
        ("divide", "7", "2", "Result: 3.5"),
        ("divide", "2", "3", "Result: 0.6666666667"),    # rounded to the precision setting
        ("power", "2", "3", "Result: 8"),
        ("root", "27", "3", "Result: 3"),
        ("modulus", "7", "3", "Result: 1"),
        ("int_divide", "7", "2", "Result: 3"),
        ("percent", "5", "10", "Result: 50"),            # not shown as 5E+1
        ("abs_diff", "3", "10", "Result: 7"),
    ])
    def test_each_operation(self, repl, command, a, b, expected):
        assert expected in repl([command, a, b, "exit"])

    def test_calculation_is_logged_and_auto_saved(self, repl, config):
        repl(["add", "1", "1", "exit"])
        assert config.history_file.exists()
        assert "Calculation: Addition(1, 1) = 2" in config.log_file.read_text()


class TestErrorMessages:
    """Known errors print a clean message and the loop keeps running."""

    @pytest.mark.parametrize("command, a, b, message", [
        ("divide", "1", "0", "Error: Division by zero is not allowed"),
        ("add", "1", "abc", "Error: Invalid number format: abc"),
        ("root", "-4", "2", "Error: Cannot calculate root of negative number"),
        ("power", "0", "-1", "Error: 0 cannot be raised to negative power"),
    ])
    def test_friendly_errors(self, repl, command, a, b, message):
        out = repl([command, a, b, "exit"])
        assert message in out
        assert "Unexpected" not in out
        assert "C U LATER" in out                         # still reached exit

    def test_unexpected_error_in_a_calculation(self, repl, monkeypatch):
        def explode(self, a, b):
            raise RuntimeError("boom")
        monkeypatch.setattr(Calculator, "perform_operation", explode)
        assert "Unexpected error: boom" in repl(["add", "1", "1", "exit"])

    def test_unexpected_error_in_the_main_loop(self, repl, monkeypatch):
        def explode(self):
            raise RuntimeError("boom")
        monkeypatch.setattr(Calculator, "show_history", explode)
        out = repl(["history", "exit"])
        assert "Error: boom" in out and "C U LATER" in out

    def test_fatal_error_on_startup(self, repl, monkeypatch, capsys):
        def broken_calculator():
            raise ConfigurationError("bad config")
        monkeypatch.setattr("app.calculator_repl.Calculator", broken_calculator)
        monkeypatch.setattr("builtins.input", lambda prompt="": "exit")
        calculator_repl()
        assert "Fatal error: bad config" in capsys.readouterr().out


class TestInterrupts:
    def test_ctrl_c_cancels_but_keeps_running(self, repl):
        out = repl([KeyboardInterrupt, "exit"])
        assert "Operation cancelled" in out and "C U LATER" in out

    def test_ctrl_c_while_entering_numbers(self, repl):
        out = repl(["add", "1", KeyboardInterrupt, "exit"])
        assert "Operation cancelled" in out and "C U LATER" in out

    def test_end_of_input_exits_cleanly(self, repl):
        assert "Input terminated" in repl([])


class TestHistoryCommands:
    def test_empty_history_message(self, repl):
        assert "No calculations in history" in repl(["history", "exit"])

    def test_history_lists_calculations_in_order(self, repl):
        out = repl(["add", "2", "3", "multiply", "4", "5", "history", "exit"])
        assert "1. Addition(2, 3) = 5" in out
        assert "2. Multiplication(4, 5) = 20" in out

    def test_undo_and_redo(self, repl):
        out = repl(["add", "2", "3", "undo", "history", "redo", "history", "exit"])
        assert "Operation undone" in out
        assert "No calculations in history" in out
        assert "Operation redone" in out
        assert "1. Addition(2, 3) = 5" in out.split("Operation redone")[1]

    def test_nothing_to_undo_or_redo(self, repl):
        out = repl(["undo", "redo", "exit"])
        assert "Nothing to undo" in out and "Nothing to redo" in out

    def test_clear(self, repl):
        out = repl(["add", "1", "1", "clear", "history", "exit"])
        assert "History cleared" in out
        assert "No calculations in history" in out.split("History cleared")[1]

    def test_clear_can_be_undone(self, repl):
        out = repl(["add", "1", "1", "clear", "undo", "history", "exit"])
        assert "1. Addition(1, 1) = 2" in out.split("Operation undone")[1]


class TestSaveAndLoadCommands:
    def test_save(self, repl, config):
        out = repl(["add", "1", "1", "save", "exit"])
        assert "History saved successfully" in out
        assert config.history_file.exists()

    def test_load_restores_saved_history(self, repl):
        """Auto-save wrote the file after the add; clear only empties memory."""
        out = repl(["add", "1", "1", "clear", "load", "history", "exit"])
        assert "History loaded successfully" in out
        assert "1. Addition(1, 1) = 2" in out.split("History loaded successfully")[1]

    def test_load_without_a_file(self, repl):
        assert "Error: No history file found" in repl(["load", "exit"])

    def test_save_failure_is_reported(self, repl, monkeypatch, tmp_path):
        monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(tmp_path))   # a folder, not a file
        assert "Error: Failed to save history" in repl(["save", "exit"])