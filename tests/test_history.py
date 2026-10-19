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

class TestAutoSaveObserver:
    """AutoSaveObserver saves the history to CSV when auto-save is on."""

    def test_requires_calculator_attributes(self):
        """The calculator must have 'config' and 'save_history'."""
        with pytest.raises(TypeError):
            AutoSaveObserver(object())

    def test_rejects_none(self, calc):
        with pytest.raises(AttributeError):
            AutoSaveObserver(calc).update(None)

    def test_saves_csv_when_enabled(self, config, calc, run):
        calc.add_observer(AutoSaveObserver(calc))
        run("add", "2", "3")
        df = pd.read_csv(config.history_file)
        assert len(df) == 1
        assert df.loc[0, "operation"] == "Addition"

    def test_file_grows_with_each_calculation(self, config, calc, run):
        """Each save rewrites the file with the full history, so it always matches memory."""
        calc.add_observer(AutoSaveObserver(calc))
        run("add", "1", "1")
        run("add", "2", "2")
        assert len(pd.read_csv(config.history_file)) == 2

    def test_does_nothing_when_disabled(self, tmp_path):
        config = CalculatorConfig(base_dir=tmp_path, auto_save=False)
        calc = Calculator(config)
        calc.add_observer(AutoSaveObserver(calc))
        calc.set_operation(OperationFactory.create_operation("add"))
        calc.perform_operation("1", "2")
        assert not config.history_file.exists()

    def test_logs_when_saved(self, config, calc, run):
        calc.add_observer(AutoSaveObserver(calc))
        run("add", "1", "1")
        assert "History auto-saved" in read_log(config)


class TestCalculatorNotifiesObservers:
    """How Calculator registers observers and tells them about calculations."""

    def test_called_once_per_successful_calculation(self, calc, run):
        observer = RecordingObserver()
        calc.add_observer(observer)
        run("add", "1", "2")
        assert len(observer.seen) == 1
        assert observer.seen[0].result == Decimal(3)

    def test_not_called_when_calculation_fails(self, calc, run):
        observer = RecordingObserver()
        calc.add_observer(observer)
        with pytest.raises(ValidationError):
            run("divide", "1", "0")
        assert observer.seen == []

    def test_all_observers_are_notified(self, calc, run):
        first, second = RecordingObserver(), RecordingObserver()
        calc.add_observer(first)
        calc.add_observer(second)
        run("add", "1", "2")
        assert len(first.seen) == 1 and len(second.seen) == 1

    def test_removed_observer_is_not_notified(self, calc, run):
        observer = RecordingObserver()
        calc.add_observer(observer)
        calc.remove_observer(observer)
        run("add", "1", "2")
        assert observer.seen == []

    def test_adding_and_removing_is_logged(self, config, calc):
        observer = RecordingObserver()
        calc.add_observer(observer)
        calc.remove_observer(observer)
        text = read_log(config)
        assert "Observer added: RecordingObserver" in text
        assert "Observer removed: RecordingObserver" in text

    def test_failing_observer_does_not_break_others(self, config, calc, run):
        """The calculation succeeds, later observers still run, and the error is logged."""
        observer = RecordingObserver()
        calc.add_observer(FailingObserver())
        calc.add_observer(observer)
        assert run("add", "1", "2") == Decimal(3)
        assert len(observer.seen) == 1
        text = read_log(config)
        assert "ERROR" in text and "observer exploded" in text

    def test_failed_autosave_does_not_fail_the_calculation(
        self, monkeypatch, tmp_path, calc, run
    ):
        """If saving fails (here: the history file path is a folder), the result still returns."""
        calc.add_observer(AutoSaveObserver(calc))
        monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(tmp_path))
        assert run("add", "1", "2") == Decimal(3)
        assert len(calc.history) == 1