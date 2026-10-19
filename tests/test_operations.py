"""
Tests for operations.py.

Each operation has its own test class. The shared BaseOperationTest runs the
valid and invalid cases that each class defines as data, so adding a new
case means adding one dictionary entry instead of writing a new test.
"""

from decimal import Decimal
from typing import Any, Dict, Optional, Type

import pytest

from app.exceptions import ValidationError
from app.operations import (
    Abs_Diff,
    Addition,
    Division,
    Int_Divide,
    Modulus,
    Multiplication,
    Operation,
    OperationFactory,
    Percent,
    Power,
    Root,
    Subtraction,
)


class TestOperation:
    """Tests for the abstract Operation base class."""

    def test_str_representation(self):
        """str(operation) returns the class name, which Calculation stores in history."""
        # A throwaway subclass, since Operation itself can't be instantiated
        class TestOp(Operation):
            def execute(self, a: Decimal, b: Decimal) -> Decimal:
                return a

        assert str(TestOp()) == "TestOp"

    def test_operation_is_abstract(self):
        """The base class can't be created directly because execute() is abstract."""
        with pytest.raises(TypeError):
            Operation()


class BaseOperationTest:
    """
    Shared test logic for every operation.

    Subclasses fill in the class attributes below. pytest collects the two
    test methods once per subclass (this base class has no "Test" prefix,
    so pytest doesn't run it on its own).
    """

    operation_class: Type[Operation]               # the operation being tested
    valid_test_cases: Dict[str, Dict[str, Any]]    # inputs that should succeed
    invalid_test_cases: Dict[str, Dict[str, Any]]  # inputs that should raise an error
    tolerance: Optional[Decimal] = None            # allowed error, for inexact math like roots

    def test_valid_operations(self):
        """Every valid case should produce the expected result."""
        operation = self.operation_class()
        for name, case in self.valid_test_cases.items():
            # Build Decimals from strings so no float noise sneaks in
            a = Decimal(str(case["a"]))
            b = Decimal(str(case["b"]))
            expected = Decimal(str(case["expected"]))
            result = operation.execute(a, b)

            if self.tolerance is None:
                assert result == expected, f"Failed case: {name}"
            else:
                # Roots use 1/b, which is rounded, so compare within a tiny tolerance
                assert abs(result - expected) < self.tolerance, f"Failed case: {name}"

    def test_invalid_operations(self):
        """Every invalid case should raise the expected error with the expected message."""
        operation = self.operation_class()
        for name, case in self.invalid_test_cases.items():
            a = Decimal(str(case["a"]))
            b = Decimal(str(case["b"]))
            error = case.get("error", ValidationError)
            # match is a regex searched inside the message, so a message prefix is enough
            error_message = case.get("message", "")

            with pytest.raises(error, match=error_message):
                operation.execute(a, b)


class TestAddition(BaseOperationTest):
    """Test Addition operation."""

    operation_class = Addition
    valid_test_cases = {
        "positive_numbers": {"a": "5", "b": "3", "expected": "8"},
        "negative_numbers": {"a": "-5", "b": "-3", "expected": "-8"},
        "mixed_signs": {"a": "-5", "b": "3", "expected": "-2"},
        "zero_sum": {"a": "5", "b": "-5", "expected": "0"},
        "decimals": {"a": "0.1", "b": "0.2", "expected": "0.3"},  # exact with Decimal, unlike floats
    }
    invalid_test_cases = {}  # Addition accepts any two numbers


class TestSubtraction(BaseOperationTest):
    """Test Subtraction operation."""

    operation_class = Subtraction
    valid_test_cases = {
        "positive_numbers": {"a": "5", "b": "3", "expected": "2"},
        "negative_numbers": {"a": "-5", "b": "-3", "expected": "-2"},
        "mixed_signs": {"a": "-5", "b": "3", "expected": "-8"},
        "negative_result": {"a": "2", "b": "3", "expected": "-1"},
        "zero_result": {"a": "5", "b": "5", "expected": "0"},
    }
    invalid_test_cases = {}  # Subtraction accepts any two numbers


class TestMultiplication(BaseOperationTest):
    """Test Multiplication operation."""

    operation_class = Multiplication
    valid_test_cases = {
        "positive_numbers": {"a": "5", "b": "3", "expected": "15"},
        "negative_numbers": {"a": "-5", "b": "-3", "expected": "15"},
        "mixed_signs": {"a": "-5", "b": "3", "expected": "-15"},
        "multiply_by_zero": {"a": "5", "b": "0", "expected": "0"},
        "decimals": {"a": "4", "b": "2.5", "expected": "10"},
    }
    invalid_test_cases = {}  # Multiplication accepts any two numbers


class TestDivision(BaseOperationTest):
    """Test Division operation."""

    operation_class = Division
    valid_test_cases = {
        "positive_numbers": {"a": "6", "b": "2", "expected": "3"},
        "negative_numbers": {"a": "-6", "b": "-2", "expected": "3"},
        "mixed_signs": {"a": "-6", "b": "2", "expected": "-3"},
        "decimal_result": {"a": "1", "b": "4", "expected": "0.25"},
        "zero_dividend": {"a": "0", "b": "5", "expected": "0"},
    }
    invalid_test_cases = {
        "divide_by_zero": {
            "a": "5",
            "b": "0",
            "error": ValidationError,
            "message": "Division by zero is not allowed",
        },
    }


class TestPower(BaseOperationTest):
    """Test Power operation."""

    operation_class = Power
    valid_test_cases = {
        "positive_base_and_exponent": {"a": "2", "b": "3", "expected": "8"},
        "zero_exponent": {"a": "5", "b": "0", "expected": "1"},      # anything to the power of 0
        "one_exponent": {"a": "5", "b": "1", "expected": "5"},
        "decimal_base": {"a": "2.5", "b": "2", "expected": "6.25"},
        "zero_base": {"a": "0", "b": "5", "expected": "0"},
        "negative_exponent": {"a": "5", "b": "-1", "expected": "0.2"},  # means 1/5
        "negative_base": {"a": "-2", "b": "3", "expected": "-8"},       # integer exponent keeps the sign
    }
    invalid_test_cases = {
        "zero_to_negative_power": {
            "a": "0",
            "b": "-1",
            "error": ValidationError,
            "message": "0 cannot be raised to negative power",  # this would be 1/0
        },
    }


class TestRoot(BaseOperationTest):
    """Test Root operation."""

    operation_class = Root
    # 1/b is rounded to 28 digits, so results can be off in the last digit
    tolerance = Decimal("1e-10")
    valid_test_cases = {
        "square_root": {"a": "9", "b": "2", "expected": "3"},
        "cube_root": {"a": "27", "b": "3", "expected": "3"},
        "fourth_root": {"a": "16", "b": "4", "expected": "2"},
        "decimal_root": {"a": "2.25", "b": "2", "expected": "1.5"},
        "zero_base": {"a": "0", "b": "2", "expected": "0"},
        "negative_degree": {"a": "8", "b": "-3", "expected": "0.5"},  # 8 ** (-1/3)
    }
    invalid_test_cases = {
        "negative_base": {
            "a": "-9",
            "b": "2",
            "error": ValidationError,
            "message": "Cannot calculate root of negative number",
        },
        "zero_root": {
            "a": "9",
            "b": "0",
            "error": ValidationError,
            "message": "Zero root is undefined",
        },
    }


class TestModulus(BaseOperationTest):
    """Test Modulus operation."""

    operation_class = Modulus
    valid_test_cases = {
        "simple_remainder": {"a": "7", "b": "3", "expected": "1"},
        "no_remainder": {"a": "6", "b": "3", "expected": "0"},
        "decimal_dividend": {"a": "7.5", "b": "2", "expected": "1.5"},
        # Decimal's % takes the sign of the dividend, unlike Python ints
        "negative_dividend": {"a": "-7", "b": "3", "expected": "-1"},
        "negative_divisor": {"a": "7", "b": "-3", "expected": "1"},
    }
    invalid_test_cases = {
        "modulus_by_zero": {
            "a": "5",
            "b": "0",
            "error": ValidationError,
            "message": "Division by zero is not allowed",
        },
    }


class TestIntDivide(BaseOperationTest):
    """Test Int_Divide operation (division that discards the fraction)."""

    operation_class = Int_Divide
    valid_test_cases = {
        "positive_numbers": {"a": "7", "b": "2", "expected": "3"},
        "negative_dividend": {"a": "-7", "b": "2", "expected": "-3"},  # truncates toward zero, not floor
        "negative_divisor": {"a": "7", "b": "-2", "expected": "-3"},
        "both_negative": {"a": "-7", "b": "-2", "expected": "3"},
        "fraction_discarded": {"a": "7.9", "b": "2", "expected": "3"},  # cut off, not rounded
        "result_is_zero": {"a": "1", "b": "-2", "expected": "0"},      # -0 compares equal to 0
    }
    invalid_test_cases = {
        "int_divide_by_zero": {
            "a": "5",
            "b": "0",
            "error": ValidationError,
            "message": "Division by zero is not allowed",
        },
    }


class TestPercent(BaseOperationTest):
    """Test Percent operation: (a / b) * 100."""

    operation_class = Percent
    valid_test_cases = {
        "half": {"a": "50", "b": "100", "expected": "50"},
        "quarter": {"a": "50", "b": "200", "expected": "25"},
        "whole_number_result": {"a": "5", "b": "10", "expected": "50"},
        "over_one_hundred": {"a": "200", "b": "100", "expected": "200"},
        "zero_numerator": {"a": "0", "b": "5", "expected": "0"},
        "negative_base": {"a": "50", "b": "-200", "expected": "-25"},  # negative b is allowed
    }
    invalid_test_cases = {
        "percent_of_zero": {
            "a": "5",
            "b": "0",
            "error": ValidationError,
            # Only the start of the message: match is a regex, and the
            # parentheses in the full message would be read as a regex group
            "message": "Cannot calculate percentage of zero",
        },
    }


class TestAbsDiff(BaseOperationTest):
    """Test Abs_Diff operation: |a - b|."""

    operation_class = Abs_Diff
    valid_test_cases = {
        "a_smaller": {"a": "3", "b": "10", "expected": "7"},
        "a_larger": {"a": "10", "b": "3", "expected": "7"},    # operand order doesn't matter
        "both_negative": {"a": "-5", "b": "-8", "expected": "3"},
        "mixed_signs": {"a": "-5", "b": "5", "expected": "10"},
        "equal_numbers": {"a": "2.5", "b": "2.5", "expected": "0"},
    }
    invalid_test_cases = {}  # any two numbers have an absolute difference