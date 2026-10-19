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