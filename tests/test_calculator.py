"""
Tests for calculator.py: running operations, history, undo/redo, and CSV save/load.

Observer behavior is tested in test_history.py, and the memento class itself
in test_calculator_memento.py. The logger doesn't propagate to caplog, so log
checks read the log file.
"""

from decimal import Decimal

import pandas as pd
import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError, OperationError, ValidationError
from app.operations import Operation, OperationFactory

CSV_COLUMNS = ["operation", "operand1", "operand2", "result", "timestamp"]


def read_log(config: CalculatorConfig) -> str:
    """Return the whole log file as text."""
    return config.log_file.read_text(encoding=config.default_encoding)


class AlwaysFails(Operation):
    """Test operation that fails with the app's own OperationError."""

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        raise OperationError("broken on purpose")


class TestInitialization:
    """A new Calculator starts empty and sets up its folders and logging."""

    def test_starts_empty(self, calc):
        assert calc.history == []
        assert calc.undo_stack == []
        assert calc.redo_stack == []
        assert calc.observers == []
        assert calc.operation_strategy is None
        assert calc.last_calculation is None

    def test_creates_log_file_and_history_folder(self, config, calc):
        assert config.log_file.exists()
        assert config.history_dir.is_dir()

    def test_invalid_config_is_rejected(self, tmp_path):
        with pytest.raises(ConfigurationError):
            Calculator(CalculatorConfig(base_dir=tmp_path, max_history_size=-1))

    def test_builds_default_config_when_none_given(self, monkeypatch, tmp_path):
        """With no config, the project root is used (redirected here to a temp folder)."""
        monkeypatch.setattr("app.calculator.get_project_root", lambda: tmp_path)
        assert Calculator().config.base_dir == tmp_path

class TestPerformOperation:
    """Validation, execution, and recording of a calculation."""

    def test_requires_an_operation(self, calc):
        with pytest.raises(OperationError, match="No operation set"):
            calc.perform_operation("1", "2")

    def test_returns_result_and_records_it(self, calc, run):
        result = run("add", "2", "3")
        assert result == Decimal(5)
        assert calc.last_calculation.result == Decimal(5)
        assert len(calc.history) == 1

    def test_accepts_numbers_as_well_as_strings(self, calc, run):
        assert run("add", 2, 3.5) == Decimal("5.5")

    def test_operation_can_be_switched(self, calc, run):
        assert run("add", "6", "2") == Decimal(8)
        assert run("divide", "6", "2") == Decimal(3)

    def test_invalid_input_changes_nothing(self, calc, run):
        with pytest.raises(ValidationError):
            run("add", "1", "abc")
        assert calc.history == [] and calc.undo_stack == []
        assert calc.last_calculation is None

    def test_too_large_input_is_rejected(self, tmp_path):
        config = CalculatorConfig(base_dir=tmp_path, max_input_value=Decimal(100))
        calc = Calculator(config)
        calc.set_operation(OperationFactory.create_operation("add"))
        with pytest.raises(ValidationError, match="exceeds maximum"):
            calc.perform_operation("101", "1")

    def test_rule_violation_changes_nothing(self, calc, run):
        """A failed calculation must not touch history, undo stack, or redo stack."""
        run("add", "1", "1")
        calc.undo()                                  # puts one entry on the redo stack
        with pytest.raises(ValidationError):
            run("divide", "1", "0")
        assert calc.history == []
        assert len(calc.undo_stack) == 0
        assert len(calc.redo_stack) == 1

    def test_decimal_math_error_becomes_operation_error(self, calc, run):
        """0 ** 0 passes the operation's checks but fails inside Decimal."""
        with pytest.raises(OperationError, match="Operation failed"):
            run("power", "0", "0")
        assert calc.history == [] and calc.undo_stack == []

    def test_operation_errors_pass_through_unchanged(self, calc):
        calc.set_operation(AlwaysFails())
        with pytest.raises(OperationError, match="broken on purpose"):
            calc.perform_operation("1", "2")
        assert calc.history == []

    def test_validation_failure_logged_as_warning(self, config, calc, run):
        with pytest.raises(ValidationError):
            run("add", "1", "abc")
        text = read_log(config)
        assert "WARNING" in text and "Validation failed" in text

    def test_operation_failure_logged_as_error(self, config, calc):
        calc.set_operation(AlwaysFails())
        with pytest.raises(OperationError):
            calc.perform_operation("1", "2")
        text = read_log(config)
        assert "ERROR" in text and "Operation failed: broken on purpose" in text

    def test_unexpected_failure_logged_as_error(self, config, calc, run):
        with pytest.raises(OperationError):
            run("power", "0", "0")
        assert "Unexpected failure" in read_log(config)

class TestHistory:
    """Showing, trimming, and clearing history."""

    def test_show_history_format(self, calc, run):
        run("add", "2", "3")
        run("multiply", "4", "5")
        assert calc.show_history() == ["Addition(2, 3) = 5", "Multiplication(4, 5) = 20"]

    def test_show_history_is_empty_at_start(self, calc):
        assert calc.show_history() == []

    def test_show_history_uses_configured_precision(self, tmp_path):
        calc = Calculator(CalculatorConfig(base_dir=tmp_path, precision=2))
        calc.set_operation(OperationFactory.create_operation("divide"))
        calc.perform_operation("2", "3")
        assert calc.show_history() == ["Division(2, 3) = 0.67"]

    def test_oldest_entry_is_dropped_past_the_limit(self, tmp_path):
        calc = Calculator(CalculatorConfig(base_dir=tmp_path, max_history_size=2))
        calc.set_operation(OperationFactory.create_operation("add"))
        for number in ("1", "2", "3"):
            calc.perform_operation(number, "0")
        assert [c.operand1 for c in calc.history] == [Decimal(2), Decimal(3)]

    def test_undo_after_trimming_restores_the_previous_window(self, tmp_path):
        calc = Calculator(CalculatorConfig(base_dir=tmp_path, max_history_size=2))
        calc.set_operation(OperationFactory.create_operation("add"))
        for number in ("1", "2", "3"):
            calc.perform_operation(number, "0")
        calc.undo()
        assert [c.operand1 for c in calc.history] == [Decimal(1), Decimal(2)]

    def test_clear_empties_history(self, calc, run):
        run("add", "1", "1")
        calc.clear_history()
        assert calc.history == []
        assert "History cleared" in read_log(calc.config)

    def test_clear_on_empty_history_is_harmless(self, calc):
        calc.clear_history()
        assert calc.history == []

class TestUndoRedo:
    """Undo and redo move between earlier and later history states."""

    def test_undo_then_redo(self, calc, run):
        run("add", "1", "1")
        assert calc.undo() is True
        assert calc.history == []
        assert calc.redo() is True
        assert len(calc.history) == 1

    def test_nothing_to_undo_or_redo(self, calc):
        assert calc.undo() is False
        assert calc.redo() is False

    @pytest.mark.parametrize("count", [1, 2, 3])
    def test_undo_all_then_redo_all(self, calc, run, count):
        for i in range(count):
            run("add", str(i), "1")
        for _ in range(count):
            assert calc.undo()
        assert calc.history == []
        assert calc.undo() is False
        for _ in range(count):
            assert calc.redo()
        assert len(calc.history) == count
        assert calc.redo() is False

    def test_new_calculation_clears_redo(self, calc, run):
        run("add", "1", "1")
        calc.undo()
        run("add", "2", "2")
        assert calc.redo() is False

    def test_clear_is_undoable(self, calc, run):
        run("add", "1", "1")
        calc.clear_history()
        calc.undo()
        assert len(calc.history) == 1

    def test_clear_discards_redo(self, calc, run):
        run("add", "1", "1")
        calc.undo()
        calc.clear_history()
        assert calc.redo() is False

    def test_undo_and_redo_are_logged(self, config, calc, run):
        run("add", "1", "1")
        calc.undo()
        calc.redo()
        text = read_log(config)
        assert "Undo performed" in text and "Redo performed" in text

    def test_nothing_to_undo_logs_warning(self, config, calc):
        calc.undo()
        text = read_log(config)
        assert "WARNING" in text and "nothing to undo" in text.lower()

    def test_nothing_to_redo_logs_warning(self, config, calc):
        calc.redo()
        assert "nothing to redo" in read_log(config).lower()


class TestSaveHistory:
    """Writing history to CSV with pandas."""

    def test_csv_has_the_required_columns(self, config, calc, run):
        run("add", "1", "2")
        calc.save_history()
        assert list(pd.read_csv(config.history_file).columns) == CSV_COLUMNS

    def test_one_row_per_calculation(self, config, calc, run):
        run("add", "1", "2")
        run("subtract", "5", "3")
        calc.save_history()
        df = pd.read_csv(config.history_file)
        assert list(df["operation"]) == ["Addition", "Subtraction"]

    def test_empty_history_writes_header_only(self, config, calc):
        calc.save_history()
        df = pd.read_csv(config.history_file)
        assert df.empty and list(df.columns) == CSV_COLUMNS

    def test_recreates_missing_history_folder(self, config, calc):
        config.history_dir.rmdir()
        calc.save_history()
        assert config.history_file.exists()

    def test_save_is_logged(self, config, calc):
        calc.save_history()
        assert "History saved" in read_log(config)

    def test_failure_raises_operation_error(self, monkeypatch, config, calc, tmp_path):
        """Pointing the history file at a folder makes writing fail."""
        monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(tmp_path))
        with pytest.raises(OperationError, match="Failed to save history"):
            calc.save_history()
        assert "Failed to save history" in read_log(config)


class TestLoadHistory:
    """Reading history back from CSV."""

    def test_round_trip_keeps_exact_values(self, config, calc, run):
        run("add", "0.1", "0.2")
        calc.save_history()

        fresh = Calculator(config)
        fresh.load_history()
        assert fresh.history[0].operand1 == Decimal("0.1")   # not float-rounded
        assert fresh.history[0].result == Decimal("0.3")

    def test_empty_history_round_trip(self, calc):
        calc.save_history()
        calc.load_history()
        assert calc.history == []

    def test_load_is_undoable(self, calc, run):
        run("add", "1", "1")
        calc.save_history()
        calc.clear_history()
        calc.load_history()
        assert len(calc.history) == 1
        calc.undo()
        assert calc.history == []

    def test_load_is_logged(self, config, calc, run):
        run("add", "1", "1")
        calc.save_history()
        calc.load_history()
        assert "Loaded 1 calculations" in read_log(config)

    def test_missing_file(self, config, calc):
        with pytest.raises(OperationError, match="No history file found"):
            calc.load_history()
        assert "Failed to load history" in read_log(config)

    @pytest.mark.parametrize("content, message", [
        ("", "empty"),
        ("a,b\n1,2\n", "missing columns"),
        ("operation,operand1\nAddition,1\nAddition,1,2,3,4,5\n", "malformed"),
        ("operation,operand1,operand2,result,timestamp\n"
         "Addition,abc,1,2,2024-01-01T00:00:00\n", "Invalid calculation data"),
    ])
    def test_bad_files(self, config, calc, content, message):
        config.history_file.write_text(content)
        with pytest.raises(OperationError, match=message):
            calc.load_history()

    def test_undecodable_file(self, config, calc):
        config.history_file.write_bytes(b"operation,operand1\n\xff\xfe,1\n")
        with pytest.raises(OperationError, match="Could not read history file"):
            calc.load_history()

    def test_unreadable_path(self, monkeypatch, calc, tmp_path):
        """A folder where the file should be can't be read."""
        monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(tmp_path))
        with pytest.raises(OperationError, match="Could not read history file"):
            calc.load_history()

    def test_failed_load_leaves_everything_unchanged(self, config, calc, run):
        run("add", "1", "1")
        config.history_file.write_text("")            # corrupt the file
        with pytest.raises(OperationError):
            calc.load_history()
        assert len(calc.history) == 1
        assert len(calc.undo_stack) == 1               # only the snapshot from the add