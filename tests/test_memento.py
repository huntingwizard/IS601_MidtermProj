"""Tests for calculator_memento.py and how Calculator uses it for undo/redo."""

import datetime
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento


class TestCalculatorMemento:
    """The snapshot class itself."""

    def test_stores_history_and_timestamp(self):
        """It keeps the calculations in order and fills in a timestamp by default."""
        calc = Calculation("Addition", Decimal(1), Decimal(2))
        before = datetime.datetime.now()
        memento = CalculatorMemento(history=(calc,))
        assert memento.history == (calc,)
        assert memento.timestamp >= before

    def test_is_immutable(self):
        """frozen=True blocks reassignment, and a tuple blocks in-place changes."""
        memento = CalculatorMemento(history=())
        with pytest.raises(FrozenInstanceError):
            memento.history = ()
        assert isinstance(memento.history, tuple)
class TestCalculatorMementoUsage:
    """How Calculator creates and restores snapshots."""

    def test_snapshot_is_unaffected_by_later_changes(self, calc, run):
        """A snapshot taken now must not change when history grows afterward."""
        run("add", "1", "1")
        snapshot = calc._snapshot()
        run("add", "2", "2")
        assert len(snapshot.history) == 1

    def test_undo_and_redo_restore_exact_states(self, calc, run):
        """Each undo/redo step restores the right earlier state, and history stays a list."""
        run("add", "1", "1")
        run("add", "2", "2")
        calc.undo()
        assert [c.operand1 for c in calc.history] == [Decimal(1)]
        calc.undo()
        assert calc.history == []
        calc.redo()
        calc.redo()
        assert [c.operand1 for c in calc.history] == [Decimal(1), Decimal(2)]
        assert isinstance(calc.history, list)