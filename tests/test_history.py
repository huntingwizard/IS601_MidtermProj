"""
Tests for history.py (the Observer pattern) and how Calculator notifies observers.

The logger writes to a file and doesn't propagate to caplog, so log checks
read the log file directly.
"""

from decimal import Decimal

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError
from app.history import AutoSaveObserver, HistoryObserver, LoggingObserver
from app.operations import OperationFactory


def read_log(config: CalculatorConfig) -> str:
    """Return the whole log file as text."""
    return config.log_file.read_text(encoding=config.default_encoding)


def make_calculation() -> Calculation:
    """A simple Addition(2, 3) = 5 to hand to observers directly."""
    return Calculation("Addition", Decimal(2), Decimal(3))


class RecordingObserver(HistoryObserver):
    """Test observer that remembers every calculation it is told about."""

    def __init__(self):
        self.seen = []

    def update(self, calculation):
        self.seen.append(calculation)


class FailingObserver(HistoryObserver):
    """Test observer that always fails, to prove one bad observer can't break the rest."""

    def update(self, calculation):
        raise RuntimeError("observer exploded")


class TestHistoryObserver:
    """The abstract interface."""

    def test_is_abstract(self):
        """update() is abstract, so the base class can't be created directly."""
        with pytest.raises(TypeError):
            HistoryObserver()
class TestLoggingObserver:
    """LoggingObserver writes each calculation to the log file."""

    def test_logs_operation_operands_and_result(self, config, calc):
        """calc is requested so the logger is set up and the log folder exists."""
        LoggingObserver().update(make_calculation())
        assert "Calculation: Addition(2, 3) = 5" in read_log(config)

    def test_logs_at_info_level(self, config, calc):
        LoggingObserver().update(make_calculation())
        assert "INFO - Calculation:" in read_log(config)

    def test_rejects_none(self):
        with pytest.raises(AttributeError):
            LoggingObserver().update(None)