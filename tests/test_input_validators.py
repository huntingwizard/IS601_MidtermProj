"""Tests for input_validators.py: converting and range-checking user input."""

from decimal import Decimal

import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError
from app.input_validators import InputValidator


@pytest.fixture
def small_config(tmp_path):
    """A config with a small max input (1000), so the limit is easy to test."""
    return CalculatorConfig(base_dir=tmp_path, max_input_value=Decimal(1000))


class TestValidNumbers:
    """Inputs that should convert to a Decimal."""

    @pytest.mark.parametrize("raw, expected", [
        ("5", Decimal(5)),
        ("-2.5", Decimal("-2.5")),
        ("0", Decimal(0)),
        ("1e2", Decimal(100)),               # scientific notation is accepted
        ("1000", Decimal(1000)),             # exactly the limit is allowed
        ("-1000", Decimal(-1000)),           # the limit applies to negatives too
    ])
    def test_strings(self, small_config, raw, expected):
        assert InputValidator.validate_number(raw, small_config) == expected

    @pytest.mark.parametrize("raw", ["  5  ", "\t5\n"])
    def test_whitespace_is_stripped(self, small_config, raw):
        assert InputValidator.validate_number(raw, small_config) == Decimal(5)

    @pytest.mark.parametrize("raw, expected", [
        (3, Decimal(3)),
        (0.1, Decimal("0.1")),               # floats go through str(), so no float noise
        (Decimal("1.5"), Decimal("1.5")),
    ])
    def test_non_string_types(self, small_config, raw, expected):
        assert InputValidator.validate_number(raw, small_config) == expected

    def test_returns_a_decimal(self, small_config):
        assert isinstance(InputValidator.validate_number("5", small_config), Decimal)


class TestInvalidNumbers:
    """Inputs that must raise ValidationError."""

    @pytest.mark.parametrize("raw", [
        "abc",
        "",
        "   ",
        "1,000",                             # commas aren't allowed
        "1.2.3",
        "5 5",
    ])
    def test_not_a_number(self, small_config, raw):
        with pytest.raises(ValidationError, match="Invalid number format"):
            InputValidator.validate_number(raw, small_config)

    @pytest.mark.parametrize("raw", ["1001", "-1001", "1e4"])
    def test_too_large(self, small_config, raw):
        with pytest.raises(ValidationError, match="exceeds maximum"):
            InputValidator.validate_number(raw, small_config)

    @pytest.mark.parametrize("raw", ["nan", "inf", "-inf", "Infinity"])
    def test_nan_and_infinity(self, small_config, raw):
        """Rejected either as too large or as invalid, but never accepted."""
        with pytest.raises(ValidationError):
            InputValidator.validate_number(raw, small_config)

    def test_original_error_is_chained(self, small_config):
        """The ValidationError keeps the original Decimal error as its cause."""
        with pytest.raises(ValidationError) as info:
            InputValidator.validate_number("abc", small_config)
        assert info.value.__cause__ is not None