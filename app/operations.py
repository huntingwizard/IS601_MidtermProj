from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict
from app.exceptions import ValidationError

class Operation(ABC):
    """
    Abstract class used to define structure of operations
    """
    
    def __str__(self) -> str:
        """
        defines how operation is called as a string, returning "str: Operation Name"
        """

        return self.__class__.__name__
    @abstractmethod
    def execute(self, a: Decimal, b: Decimal) -> Decimal:

        "defines the structure of what happens when an operation is executed. returns a Decimal when given two input Decimals"
        pass # pragma: no cover
    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        "defines the structure of the validotor of operation inputs. takes in the operands and returns nothing."
        pass


class Addition(Operation):
    """
    Addition operation implementation.

    Performs the addition of two numbers.
    """

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Add two numbers.
        Takes two decimal inputs and outputs 1 decimal
        a + b = c
        """
        self.validate_operands(a, b)
        return a + b


class Subtraction(Operation):
    """
    Subtraction operation implementation.

    Performs the subtraction of one number from another.
    """

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Subtract number b from number a
        Takes two decimal inputs and outputs 1 decimal
        a - b = c
        """
        self.validate_operands(a, b)
        return a - b


class Multiplication(Operation):
    """
    Multiplication operation implementation.

    Performs the multiplication of two numbers.
    """

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        multiply two numbers.
        Takes two decimal inputs and outputs 1 decimal
        a * b = c
        """
        self.validate_operands(a, b)
        return a * b


class Division(Operation):
    """
    Division operation implementation.

    Performs the division of one number by another.
    """

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        """
        Validates operands
        checks if b is 0 and if it is raises Divide by 0

        a is the dividend, b is divisor
        """
        super().validate_operands(a, b)
        if b == 0:
            raise ValidationError("Division by zero is not allowed")

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Divide number a from number b
        Takes two decimal inputs and outputs 1 decimal
        a / b = c
        
        Raises divide by 0 error if b is 0
        """
        self.validate_operands(a, b)
        return a / b


class Power(Operation):
    """
    Power (exponentiation) operation implementation.

    Raises one number to the power of another.
    """
    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        """
        Validates operands for Power operation
        raises Divide by 0 error when exponent b is negative and base a is 0
       """
        super().validate_operands(a, b)
        if b < 0 and a==0:
            raise ValidationError("0 cannot be raised to negative power")
    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        raises number a to the power of number b
        takes two decimal inputs and returns one decimal output
        a^b=c
        """
        self.validate_operands(a, b)
        return a**b


class Root(Operation):
    """
    Root operation implementation.

    Calculates the nth root of a number.
    """

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        """
        Validate operands for root operation.

        verifies that a is not a negative number and b is not 0
        """
        super().validate_operands(a, b)
        if a < 0:
            raise ValidationError("Cannot calculate root of negative number")
        if b == 0:
            raise ValidationError("Zero root is undefined")

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        roots number a by number b
        takes two decimal numbers and retursn one decimal number
        a^(1/b)
        """
        self.validate_operands(a, b)
        return a**(1/b)


class Modulus(Operation):
    """
    Modulus operation implementation.

    Performs the modulus of one number by another.
    """
    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        """
        Validates operands
        checks if b is 0 and if it is raises Divide by 0

        a is the dividend, b is divisor
        """
        super().validate_operands(a, b)
        if b == 0:
            raise ValidationError("Division by zero is not allowed")

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Divide number a from number b and returns the remainder
        Takes two decimal inputs and outputs 1 decimal
        a % b = c
        
        Raises divide by 0 error if b is 0
        """
        self.validate_operands(a, b)
        return a % b
class Int_Divide(Operation):
    """
    Integer Division operation implementation.

    Performs the division of one number by another.
    """

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        """
        Validates operands
        checks if b is 0 and if it is raises Divide by 0

        a is the dividend, b is divisor
        """
        super().validate_operands(a, b)
        if b == 0:
            raise ValidationError("Division by zero is not allowed")

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Divide number a from number b
        Takes two decimal inputs and outputs 1 decimal
        a / b = c
        
        Raises divide by 0 error if b is 0
        """
        self.validate_operands(a, b)
        return a//b
class Percent(Operation):
    """
    Percentage operation implementation.

    Calculates what percentage a is of b: (a / b) * 100.
    """

    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        """
        Validate operands, checking for division by zero.

        Raises:
            ValidationError: If b is zero.
        """
        super().validate_operands(a, b)
        if b == 0:
            raise ValidationError("Cannot calculate percentage of zero (b cannot be 0)")

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Return a as a percentage of b.
        takes two decimal number inputs and returns one decimal number output
        """
        self.validate_operands(a, b)
        return (a * 100) / b


class Abs_Diff(Operation):
    """
    Absolute difference operation implementation.

    Calculates the non-negative distance between two numbers: |a - b|.
    """

    def execute(self, a: Decimal, b: Decimal) -> Decimal:
        """
        Return the absolute difference between a and b.
        """
        self.validate_operands(a, b)
        return abs(a - b)
    
class OperationFactory:
    """
    Factory class for creating operation instances.

    Implements the Factory pattern by providing a method to instantiate
    different operation classes based on a given operation type. This promotes
    scalability and decouples the creation logic from the Calculator class.
    """

    # Dictionary mapping operation identifiers to their corresponding classes
    _operations: Dict[str, type] = {
        'add': Addition,
        'subtract': Subtraction,
        'multiply': Multiplication,
        'divide': Division,
        'power': Power,
        'root': Root,
        'modulus': Modulus,
        'int_divide': Int_Divide,
        'percent': Percent,
        'abs_diff': Abs_Diff,
    }

    @classmethod
    def register_operation(cls, name: str, operation_class: type) -> None:
        """
        Register a new operation type.

        Allows dynamic addition of new operations to the factory.

        Args:
            name (str): Operation identifier (e.g., 'modulus').
            operation_class (type): The class implementing the new operation.

        Raises:
            TypeError: If the operation_class does not inherit from Operation.
        """
        if not issubclass(operation_class, Operation):
            raise TypeError("Operation class must inherit from Operation")
        cls._operations[name.lower()] = operation_class

    @classmethod
    def create_operation(cls, operation_type: str) -> Operation:
        """
        Create an operation instance based on the operation type.

        This method retrieves the appropriate operation class from the
        _operations dictionary and instantiates it.

        Args:
            operation_type (str): The type of operation to create (e.g., 'add').

        Returns:
            Operation: An instance of the specified operation class.

        Raises:
            ValueError: If the operation type is unknown.
        """
        operation_class = cls._operations.get(operation_type.lower())
        if not operation_class:
            raise ValueError(f"Unknown operation: {operation_type}")
        return operation_class()
