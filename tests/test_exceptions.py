"""Tests for exceptions.py: the custom exception hierarchy."""

import pytest

from app.exceptions import (
    CalculatorError,
    ConfigurationError,
    OperationError,
    ValidationError,
)

SPECIFIC_ERRORS = [ValidationError, OperationError, ConfigurationError]


class TestHierarchy:
    """Every custom error inherits from CalculatorError, which inherits from Exception."""

    def test_base_is_an_exception(self):
        assert issubclass(CalculatorError, Exception)

    @pytest.mark.parametrize("error_class", SPECIFIC_ERRORS)
    def test_specific_errors_inherit_from_base(self, error_class):
        assert issubclass(error_class, CalculatorError)

    @pytest.mark.parametrize("first, second", [
        (ValidationError, OperationError),
        (OperationError, ValidationError),
        (ValidationError, ConfigurationError),
        (ConfigurationError, OperationError),
    ])
    def test_siblings_are_independent(self, first, second):
        """Catching one kind of error must not accidentally catch another."""
        assert not issubclass(first, second)


class TestRaising:
    """The errors can be raised, caught, and carry their message."""

    @pytest.mark.parametrize("error_class", SPECIFIC_ERRORS)
    def test_message_is_preserved(self, error_class):
        with pytest.raises(error_class) as info:
            raise error_class("something went wrong")
        assert str(info.value) == "something went wrong"

    @pytest.mark.parametrize("error_class", SPECIFIC_ERRORS)
    def test_base_class_catches_every_specific_error(self, error_class):
        """The REPL relies on this to handle all app errors in one place."""
        with pytest.raises(CalculatorError):
            raise error_class("caught by the base class")

    def test_wrong_handler_does_not_catch(self):
        """An OperationError handler lets a ValidationError pass through."""
        with pytest.raises(ValidationError):
            try:
                raise ValidationError("bad input")
            except OperationError:  # pragma: no cover (must not run)
                pytest.fail("OperationError handler caught a ValidationError")

    def test_original_cause_can_be_chained(self):
        """'raise ... from ...' keeps the underlying error, as InputValidator does."""
        with pytest.raises(ValidationError) as info:
            try:
                int("abc")
            except ValueError as original:
                raise ValidationError("not a number") from original
        assert isinstance(info.value.__cause__, ValueError)