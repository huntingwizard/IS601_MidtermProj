from dataclasses import dataclass, field
import datetime
from decimal import Decimal, InvalidOperation
import logging
from typing import Any, Dict

from app.exceptions import OperationError

@dataclass
class Calculation:
    """
    Value object created each time a calculation is made holding the specific operation being performed their specific operands along with the result and timestamp.
    """

    #required inputs
    operation: str
    operand1: Decimal
    operand2: Decimal

    # Fields with default/calculated values
    result: Decimal = field(init=False)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __post_init__(self):
        """
        performs calculation after all fields andmethods initialized.
        """
        self.result=self.calculate()
    def calculate(self) -> Decimal:
        """
        Executes the calculation utilizing a map of each supported operation

        returns a decimal or raises an error.
        """
        operations = {
            "Addition": lambda x, y: x + y,
            "Subtraction": lambda x, y: x - y,
            "Multiplication": lambda x, y: x * y,
            "Division": lambda x, y: x / y if y != 0 else self._raise_div_zero(),
            "Power": lambda x, y: x**y,
            "Root": lambda x, y: (
                Decimal(pow(float(x), 1 / float(y))) 
                if x >= 0 and y != 0 
                else self._raise_invalid_root(x, y)
            ),
            "Modulus": lambda x, y: x % y if y != 0 else self._raise_div_zero(),
            "Int_Divide":lambda x, y: x // y if y != 0 else self._raise_div_zero(),
            "Percent": lambda x, y: (x*100) / y if y != 0 else self._raise_div_zero(),
            "Abs_Diff": lambda x, y: abs(x - y)
        }

        # Retrieve the operation function based on the operation name
        op = operations.get(self.operation)
        if not op:
            raise OperationError(f"Unknown operation: {self.operation}")

        try:
            # Execute the operation with the provided operands
            return op(self.operand1, self.operand2)
        except (InvalidOperation, ValueError, ArithmeticError) as e:
            # Handle any errors that occur during calculation
            raise OperationError(f"Calculation failed: {str(e)}")
    