from dataclasses import dataclass, field
import datetime
from decimal import Decimal, InvalidOperation
import logging
from typing import Any, Dict

from app.exceptions import OperationError, ValidationError
from app.operations import Operation

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
        op_class = {cls.__name__: cls for cls in Operation.__subclasses__()}.get(self.operation)
        if op_class is None:
            raise OperationError(f"Unknown operation: {self.operation}")

        try:
            return op_class().execute(self.operand1, self.operand2)
        except (InvalidOperation, ValueError, ArithmeticError) as e:
            # Handle any errors that occur during calculation
            raise OperationError(f"Calculation failed: {str(e)}")
    @staticmethod
    def _raise_div_zero():
        """
        Helper method to raise division by zero error.

        This method is called when a division by zero is attempted.
        """
        raise OperationError("Division by zero is not allowed")

    @staticmethod
    def _raise_neg_power(): 
        """
        Helper method to raise negative power error.

        This method is called when a negative exponent is used in a power operation.
        """
        raise OperationError("Negative exponents are not supported")

    @staticmethod
    def _raise_invalid_root(x: Decimal, y: Decimal): 
        """
        Helper method to raise invalid root error.

        This method is called when an invalid root operation is attempted, such as
        taking the root of a negative number or using zero as the root degree.

        Args:
            x (Decimal): The number from which the root is taken.
            y (Decimal): The degree of the root.
        """
        if y == 0:
            raise OperationError("Zero root is undefined")
        if x < 0:
            raise OperationError("Cannot calculate root of negative number")
        raise OperationError("Invalid root operation")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert calculation to dictionary for serialization.
        takes information from Calculation instance and formats it into a dictionar for storage and retrieval
    
        Returns:
            Dict[str, Any]: A dictionary containing the calculation data in a serializable format.
        """
        return {
            'operation': self.operation,
            'operand1': str(self.operand1),
            'operand2': str(self.operand2),
            'result': str(self.result),
            'timestamp': self.timestamp.isoformat()
        }
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Calculation':
        """
        Takes information from Dictionary and Creates Calculation instance

        Args:
            data (Dict[str, Any]): Dictionary containing calculation data.

        Returns:
            Calculation: A new instance of Calculation with data populated from the dictionary.

        Raises:
            OperationError: If data is invalid or missing required fields.
        """
        try:
            # Create the calculation object with the original operands
            calc = Calculation(
                operation=data['operation'],
                operand1=Decimal(data['operand1']),
                operand2=Decimal(data['operand2'])
            )

            # Set the timestamp from the saved data
            calc.timestamp = datetime.datetime.fromisoformat(data['timestamp'])
            # Verify the result matches (helps catch data corruption)
            saved_result = Decimal(data['result'])
            if calc.result != saved_result:
                logging.warning(
                    f"Loaded calculation result {saved_result} "
                    f"differs from computed result {calc.result}"
                )
            return calc
        except (KeyError, InvalidOperation, ValueError) as e:
            raise OperationError(f"Invalid calculation data: {str(e)}")
        
    def __str__(self)-> str:
        """
        defines how Calculation is represented as a string
        """
        return f"{self.operation}({self.operand1}, {self.operand2}) = {self.result}"
    def __repr__(self) -> str:
        """
        Return detailed string representation of calculation.

        Provides a detailed and unambiguous string representation of the Calculation
        instance, useful for debugging.

        Returns:
            str: Detailed string showing all calculation attributes.
        """
        return (
            f"Calculation(operation='{self.operation}', "
            f"operand1={self.operand1}, "
            f"operand2={self.operand2}, "
            f"result={self.result}, "
            f"timestamp='{self.timestamp.isoformat()}')"
        )
    def __eq__(self, other: object) -> bool:
        """
        Check if two calculations are equal.

        Compares Operation, operands, and results to determine if two Calculation instances are equal

        Args:
            other (object): Another calculation to compare with.

        Returns:
            bool: True if calculations are equal, False otherwise.
        """
        if not isinstance(other, Calculation):
            return NotImplemented
        return (
            self.operation == other.operation and
            self.operand1 == other.operand1 and
            self.operand2 == other.operand2 and
            self.result == other.result
        )
    def format_result(self, precision: int = 10) -> str:
        """
        Format the calculation result with specified precision.

        This method formats the result to a fixed number of decimal places,
        removing any trailing zeros for a cleaner presentation.

        Args:
            precision (int, optional): Number of decimal places to show. Defaults to 10.

        Returns:
            str: Formatted string representation of the result.
        """
        try:
            rounded = self.result.quantize(Decimal(1).scaleb(-precision))
            return f"{(rounded + 0).normalize():f}"
        except InvalidOperation:  # pragma: no cover
            return f"{self.result:f}"