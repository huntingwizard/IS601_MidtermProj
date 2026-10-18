from abc import ABC, abstractmethod
from typing import Any

from app.calculation import Calculation
from app.logger import get_logger


class HistoryObserver(ABC):
    """Interface for anything that reacts to a new calculation."""

    @abstractmethod
    def update(self, calculation: Calculation) -> None:
        pass  # pragma: no cover


class LoggingObserver(HistoryObserver):
    """Writes each calculation (operation, operands, result) to the log file."""

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        get_logger().info(
            "Calculation: %s(%s, %s) = %s",
            calculation.operation, calculation.operand1,
            calculation.operand2, calculation.result,
        )


class AutoSaveObserver(HistoryObserver):
    """Saves the history to CSV after each calculation when auto-save is on."""

    def __init__(self, calculator: Any):
        if not hasattr(calculator, "config") or not hasattr(calculator, "save_history"):
            raise TypeError("Calculator must have 'config' and 'save_history' attributes")
        self.calculator = calculator

    def update(self, calculation: Calculation) -> None:
        if calculation is None:
            raise AttributeError("Calculation cannot be None")
        if self.calculator.config.auto_save:
            self.calculator.save_history()
            get_logger().info("History auto-saved")