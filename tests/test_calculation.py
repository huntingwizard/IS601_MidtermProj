"""
Tests for calculation.py: the Calculation value object.

Calculation runs the operation by looking up the Operation class whose name
matches the stored operation string (for example "Int_Divide").
"""

import datetime
import logging
from decimal import Decimal

import pytest

from app.calculation import Calculation
from app.exceptions import OperationError, ValidationError


def make(op: str = "Addition", a: str = "1", b: str = "2") -> Calculation:
    """Small helper so tests stay short."""
    return Calculation(op, Decimal(a), Decimal(b))


class TestCalculate:
    """The result is computed automatically when the object is created."""

    @pytest.mark.parametrize("op, a, b, expected", [
        ("Addition", "2", "3", "5"),
        ("Subtraction", "2", "3", "-1"),
        ("Multiplication", "4", "2.5", "10"),
        ("Division", "7", "2", "3.5"),
        ("Power", "2", "3", "8"),
        ("Power", "5", "-1", "0.2"),
        ("Modulus", "7", "3", "1"),
        ("Int_Divide", "7", "2", "3"),
        ("Int_Divide", "7", "-2", "-3"),
        ("Percent", "50", "200", "25"),
        ("Abs_Diff", "3", "10", "7"),
    ])
    def test_results(self, op, a, b, expected):
        assert make(op, a, b).result == Decimal(expected)

    def test_root_result(self):
        """Roots use 1/b, which is rounded, so compare within a tiny tolerance."""
        assert abs(make("Root", "27", "3").result - Decimal(3)) < Decimal("1e-10")

    def test_every_operation_class_is_found(self):
        """Each class name used by the factory must be known to Calculation."""
        for name in ("Addition", "Subtraction", "Multiplication", "Division", "Power",
                     "Root", "Modulus", "Int_Divide", "Percent", "Abs_Diff"):
            make(name, "4", "2")  # raises OperationError if the name isn't found

    def test_timestamp_is_set_automatically(self):
        before = datetime.datetime.now()
        calc = make()
        assert before <= calc.timestamp <= datetime.datetime.now()


class TestCalculationErrors:
    """Bad operations and bad math fail with the app's own exceptions."""

    def test_unknown_operation(self):
        with pytest.raises(OperationError, match="Unknown operation: Sqrt"):
            make("Sqrt")

    @pytest.mark.parametrize("op, a, b", [
        ("Division", "1", "0"),
        ("Modulus", "1", "0"),
        ("Int_Divide", "1", "0"),
        ("Percent", "1", "0"),
        ("Root", "-4", "2"),
        ("Root", "4", "0"),
        ("Power", "0", "-1"),
    ])
    def test_rule_violations_raise_validation_error(self, op, a, b):
        """The Operation class's own checks run, so these are ValidationErrors."""
        with pytest.raises(ValidationError):
            make(op, a, b)

    @pytest.mark.parametrize("op, a, b", [
        ("Power", "0", "0"),        # Decimal can't compute 0 ** 0
        ("Power", "-8", "0.5"),     # negative base with a fractional exponent
    ])
    def test_decimal_math_errors_become_operation_errors(self, op, a, b):
        """Raw Decimal errors are wrapped so callers only see OperationError."""
        with pytest.raises(OperationError, match="Calculation failed"):
            make(op, a, b)