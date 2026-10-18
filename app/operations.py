from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict
from app.exceptions import ValidationError

class Operation(ABC):
    """
    Abstract class used to define structure of operations
    """
    @abstractmethod
    def __str__(self) -> str:
        """
        defines how operation is called as a string, returning "str: Operation Name"
        """

        return self.__class__.__name__
    def execute(self, a: Decimal, b: Decimal) -> Decimal:

        "defines the structure of what happens when an operation is executed. returns a Decimal when given two input Decimals"
        pass
    def validate_operands(self, a: Decimal, b: Decimal) -> None:
        "defines the structure of the validotor of operation inputs. takes in the operands and returns nothing."
        pass
