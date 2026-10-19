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