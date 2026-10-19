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
