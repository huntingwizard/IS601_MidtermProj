
from decimal import Decimal
from pathlib import Path
from typing import Optional, Union

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.exceptions import CalculatorError, OperationError
from app.input_validators import InputValidator
from app.operations import Operation

Number = Union[int, float, Decimal]
CalcRes = Union[Number, str]


class Calculator:
    """
    Core calculator class.

    Holds the current operation, validates the inputs, runs the operation,
    and returns the result. History, logging, and undo/redo come later.
    """

    def __init__(self, config: Optional[CalculatorConfig] = None):
        """
        Set up the calculator with a configuration.

        If no config is given, one is built from the project root folder
        (which also loads settings from the .env file).
        """
        if config is None:
            project_root = Path(__file__).parent.parent
            config = CalculatorConfig(base_dir=project_root)

        self.config = config
        self.config.validate()

        self.operation_strategy: Optional[Operation] = None
        self.last_calculation: Optional[Calculation] = None

    def set_operation(self, operation: Operation) -> None:
        """Choose which operation the next calculation will use."""
        self.operation_strategy = operation

    def perform_operation(self, a: Union[str, Number], b: Union[str, Number]) -> CalcRes:
        """
        Validate inputs, run the current operation, and return the result.

        Args:
            a: First operand (string or number).
            b: Second operand (string or number).

        Returns:
            The result of the operation.

        Raises:
            OperationError: If no operation is set or the calculation fails.
            ValidationError: If an input is not a valid number or is too large.
        """
        if not self.operation_strategy:
            raise OperationError("No operation set")

        # Validation and operation errors already use our own exception types,
        # so let them pass through unchanged
        validated_a = InputValidator.validate_number(a, self.config)
        validated_b = InputValidator.validate_number(b, self.config)

        try:
            result = self.operation_strategy.execute(validated_a, validated_b)

            # Build a Calculation too, so calculation.py gets exercised
            self.last_calculation = Calculation(
                operation=str(self.operation_strategy),
                operand1=validated_a,
                operand2=validated_b,
            )
            return result

        except CalculatorError:
            raise
        except Exception as e:
            # Anything unexpected (e.g. Decimal overflow) becomes a friendly error
            raise OperationError(f"Operation failed: {e}")