########################
# Exception Hierarchy  #
########################

class CalculatorError(Exception):
    """
    Base exception class for calculator-specific errors.

    All custom exceptions for the calculator application inherit from this class,
    allowing for unified error handling.
    """
    pass


class ValidationError(CalculatorError):
    """
    base Input validation error, Raised when user inputs something that isn't meant to be put into a calculator or exceeds input size.
    """
    pass


class OperationError(CalculatorError):
    """
    base operation error that triggers when the calculation of an operation fails, this could be due to divide by zero errors or an invalid/unsupported operation
    """
    pass


class ConfigurationError(CalculatorError):
    """
    Raised when calculator configuration is invalid.

    This could be things like impropper paths, invalid configurations, or something else. Check .env
    """
    pass
