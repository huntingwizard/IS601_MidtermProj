"""Tests for operations.py: one section per Operation class, plus the OperationFactory."""

from decimal import Decimal as D

import pytest

from app.exceptions import ValidationError
from app.operations import (
    Abs_Diff, Addition, Division, Int_Divide, Modulus, Multiplication,
    Operation, OperationFactory, Percent, Power, Root, Subtraction,
)

# ---------- Addition ----------
@pytest.mark.parametrize("a, b, expected", [
    ("2", "3", "5"),
    ("-2", "3", "1"),
    ("0.1", "0.2", "0.3"),                 # exact with Decimal, unlike floats
])
def test_addition(a, b, expected):
    assert Addition().execute(D(a), D(b)) == D(expected)

# ---------- Subtraction ----------
@pytest.mark.parametrize("a, b, expected", [
    ("3", "2", "1"),
    ("2", "3", "-1"),
    ("-2", "-3", "1"),
])
def test_subtraction(a, b, expected):
    assert Subtraction().execute(D(a), D(b)) == D(expected)


# ---------- Multiplication ----------
@pytest.mark.parametrize("a, b, expected", [
    ("4", "2.5", "10"),
    ("-3", "3", "-9"),
    ("5", "0", "0"),
])
def test_multiplication(a, b, expected):
    assert Multiplication().execute(D(a), D(b)) == D(expected)


# ---------- Division ----------
@pytest.mark.parametrize("a, b, expected", [
    ("7", "2", "3.5"),
    ("-9", "3", "-3"),
    ("1", "4", "0.25"),
])
def test_division(a, b, expected):
    assert Division().execute(D(a), D(b)) == D(expected)

# ---------- Power ----------
@pytest.mark.parametrize("a, b, expected", [
    ("2", "3", "8"),
    ("5", "-1", "0.2"),                    # negative exponent
    ("2", "0", "1"),                       # anything to the power of 0
    ("-2", "3", "-8"),                     # negative base, integer exponent
])
def test_power(a, b, expected):
    assert Power().execute(D(a), D(b)) == D(expected)

# ---------- Root ----------
# 1/b is rounded to 28 digits, so compare with a tiny tolerance instead of ==
@pytest.mark.parametrize("a, b, expected", [
    ("9", "2", "3"),
    ("27", "3", "3"),
    ("0", "2", "0"),
    ("8", "-3", "0.5"),                    # negative root degree
])
def test_root(a, b, expected):
    assert abs(Root().execute(D(a), D(b)) - D(expected)) < D("1e-10")

# ---------- Integer division ----------
@pytest.mark.parametrize("a, b, expected", [
    ("7", "2", "3"),
    ("-7", "2", "-3"),                     # truncates toward zero, not floor
    ("7", "-2", "-3"),                     # negative divisor
    ("-7", "-2", "3"),
    ("7.9", "2", "3"),                     # fraction is discarded, not rounded
    ("1", "-2", "0"),                      # -0 compares equal to 0
])
def test_int_divide(a, b, expected):
    assert Int_Divide().execute(D(a), D(b)) == D(expected)

# ---------- Percent ----------
@pytest.mark.parametrize("a, b, expected", [
    ("50", "200", "25"),
    ("5", "10", "50"),
    ("200", "100", "200"),
    ("50", "-200", "-25"),                 # negative b is allowed
])
def test_percent(a, b, expected):
    assert Percent().execute(D(a), D(b)) == D(expected)

# ---------- Absolute difference ----------
@pytest.mark.parametrize("a, b, expected", [
    ("3", "10", "7"),
    ("10", "3", "7"),                      # order of operands doesn't matter
    ("-5", "-8", "3"),
    ("2.5", "2.5", "0"),
])
def test_abs_diff(a, b, expected):
    assert Abs_Diff().execute(D(a), D(b)) == D(expected)