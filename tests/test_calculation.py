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
class TestSerialization:
    """to_dict and from_dict are used for the CSV history."""

    def test_to_dict_values(self):
        data = make("Multiplication", "1.5", "2").to_dict()
        assert data["operation"] == "Multiplication"
        assert data["operand1"] == "1.5"
        assert data["operand2"] == "2"
        assert data["result"] == "3.0"
        datetime.datetime.fromisoformat(data["timestamp"])  # must be valid ISO text

    def test_round_trip(self):
        """to_dict then from_dict gives back an equal Calculation with the same timestamp."""
        original = make("Multiplication", "1.5", "2")
        restored = Calculation.from_dict(original.to_dict())
        assert restored == original
        assert restored.timestamp == original.timestamp

    @pytest.mark.parametrize("bad_data", [
        {},                                                         # missing keys
        {"operation": "Addition", "operand1": "x", "operand2": "1",
         "result": "1", "timestamp": "2024-01-01T00:00:00"},        # operand isn't a number
        {"operation": "Addition", "operand1": "1", "operand2": "1",
         "result": "2", "timestamp": "not a date"},                 # bad timestamp
        {"operation": "Addition", "operand1": "1", "operand2": "1",
         "result": "two", "timestamp": "2024-01-01T00:00:00"},      # result isn't a number
    ])
    def test_from_dict_rejects_bad_data(self, bad_data):
        with pytest.raises(OperationError, match="Invalid calculation data"):
            Calculation.from_dict(bad_data)

    def test_mismatched_saved_result_warns_and_recomputes(self, caplog):
        """A wrong saved result is logged, and the result is recomputed from the operands."""
        data = make("Addition", "1", "1").to_dict()
        data["result"] = "999"
        with caplog.at_level(logging.WARNING):
            restored = Calculation.from_dict(data)
        assert restored.result == Decimal(2)
        assert "differs from computed result" in caplog.text

class TestComparisonAndDisplay:
    """__eq__, __str__, and __repr__."""

    def test_equal_when_operation_operands_and_result_match(self):
        assert make("Addition", "1", "2") == make("Addition", "1", "2")

    def test_timestamp_is_ignored_in_equality(self):
        first = make()
        second = make()
        second.timestamp = first.timestamp + datetime.timedelta(days=1)
        assert first == second

    @pytest.mark.parametrize("other", [
        make("Subtraction", "1", "2"),      # different operation
        make("Addition", "1", "3"),         # different operand
        "not a calculation",                # different type
    ])
    def test_not_equal(self, other):
        assert make("Addition", "1", "2") != other

    def test_str(self):
        assert str(make("Addition", "1", "2")) == "Addition(1, 2) = 3"

    def test_repr_shows_every_field(self):
        text = repr(make("Addition", "1", "2"))
        for part in ("operation='Addition'", "operand1=1", "operand2=2", "result=3", "timestamp="):
            assert part in text


class TestFormatResult:
    """format_result rounds to a number of decimal places and avoids 5E+1 and -0."""

    @pytest.mark.parametrize("op, a, b, precision, expected", [
        ("Division", "2", "3", 4, "0.6667"),
        ("Division", "2", "3", 10, "0.6666666667"),
        ("Percent", "5", "10", 10, "50"),            # no scientific notation
        ("Addition", "0.1", "0.2", 10, "0.3"),       # trailing zeros removed
        ("Int_Divide", "1", "-2", 10, "0"),          # no negative zero
        ("Addition", "1.23456", "0", 2, "1.23"),
    ])
    def test_formatting(self, op, a, b, precision, expected):
        assert make(op, a, b).format_result(precision) == expected

    def test_default_precision_is_ten(self):
        assert make("Division", "2", "3").format_result() == "0.6666666667"

    def test_stored_result_is_not_rounded(self):
        """Only the display is rounded; the stored value keeps full precision."""
        calc = make("Division", "2", "3")
        calc.format_result(2)
        assert len(str(calc.result)) > 10