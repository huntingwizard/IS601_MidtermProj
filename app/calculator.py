from decimal import Decimal
from typing import List, Optional, Union

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig, get_project_root
from app.calculator_memento import CalculatorMemento
from app.exceptions import CalculatorError, OperationError, ValidationError
from app.history import HistoryObserver
from app.input_validators import InputValidator
from app.logger import setup_logging
from app.operations import Operation

Number = Union[int, float, Decimal]
CSV_COLUMNS = ["operation", "operand1", "operand2", "result", "timestamp"]


class Calculator:
    """Runs operations, keeps history with undo/redo, and notifies observers."""

    def __init__(self, config: Optional[CalculatorConfig] = None):
        self.config = config or CalculatorConfig(base_dir=get_project_root())
        self.config.validate()
        self.logger = setup_logging(self.config)
        self.config.history_dir.mkdir(parents=True, exist_ok=True)

        self.operation_strategy: Optional[Operation] = None
        self.history: List[Calculation] = []
        self.observers: List[HistoryObserver] = []
        self.undo_stack: List[CalculatorMemento] = []
        self.redo_stack: List[CalculatorMemento] = []
        self.last_calculation: Optional[Calculation] = None

    # ---------- Observer pattern ----------
    def add_observer(self, observer: HistoryObserver) -> None:
        self.observers.append(observer)
        self.logger.info("Observer added: %s", observer.__class__.__name__)

    def remove_observer(self, observer: HistoryObserver) -> None:
        self.observers.remove(observer)
        self.logger.info("Observer removed: %s", observer.__class__.__name__)

    def notify_observers(self, calculation: Calculation) -> None:
        """Tell every observer; one failing observer must not stop the rest."""
        for observer in self.observers:
            try:
                observer.update(calculation)
            except Exception as e:
                self.logger.error("Observer %s failed: %s", observer.__class__.__name__, e)

    # ---------- Calculations ----------
    def set_operation(self, operation: Operation) -> None:
        self.operation_strategy = operation

    def perform_operation(self, a: Union[str, Number], b: Union[str, Number]) -> Decimal:
        #executes operation noted using number a and number b
        if not self.operation_strategy:
            raise OperationError("No operation set")
        try:
            x = InputValidator.validate_number(a, self.config)
            y = InputValidator.validate_number(b, self.config)
            result = self.operation_strategy.execute(x, y)
            calculation = Calculation(str(self.operation_strategy), x, y)
        except ValidationError as e:
            self.logger.warning("Validation failed: %s", e)
            raise
        except CalculatorError as e:
            self.logger.error("Operation failed: %s", e)
            raise
        except Exception as e:
            self.logger.error("Unexpected failure: %s", e)
            raise OperationError(f"Operation failed: {e}")

        self._record(calculation) #adds calculation to history
        return result

    def _record(self, calculation: Calculation) -> None:
        """Snapshot, update history, then notify (only reached on success)."""
        self.last_calculation = calculation
        self._push_undo()
        self.redo_stack.clear()
        self.history.append(calculation)
        if len(self.history) > self.config.max_history_size:
            self.history = self.history[-self.config.max_history_size:]
        self.notify_observers(calculation)

    # ---------- Memento pattern ----------
    def _snapshot(self) -> CalculatorMemento:
        return CalculatorMemento(tuple(self.history))

    def _push_undo(self) -> None:
        self.undo_stack.append(self._snapshot())

    def undo(self) -> bool:
        if not self.undo_stack:
            self.logger.warning("Undo requested but nothing to undo")
            return False
        self.redo_stack.append(self._snapshot())
        self.history = list(self.undo_stack.pop().history)
        self.logger.info("Undo performed; history has %d entries", len(self.history))
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            self.logger.warning("Redo requested but nothing to redo")
            return False
        self._push_undo()
        self.history = list(self.redo_stack.pop().history)
        self.logger.info("Redo performed; history has %d entries", len(self.history))
        return True

    # ---------- History ----------
    def show_history(self) -> List[str]:
        #formats history into clean view
        return [
            f"{c.operation}({c.operand1:f}, {c.operand2:f}) = "
            f"{c.format_result(self.config.precision)}"
            for c in self.history
        ]

    def clear_history(self) -> None:
        """Undoable: the old history is snapshotted first."""
        self._push_undo()
        self.redo_stack.clear()
        self.history.clear()
        self.logger.info("History cleared")

    # ---------- Persistence (pandas) ----------
    def save_history(self) -> None:
        #writes history to csv file
        try:
            self.config.history_dir.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame([c.to_dict() for c in self.history], columns=CSV_COLUMNS)
            df.to_csv(self.config.history_file, index=False,
                      encoding=self.config.default_encoding)
            self.logger.info("History saved (%d rows)", len(df))
        except Exception as e:
            self.logger.error("Failed to save history: %s", e)
            raise OperationError(f"Failed to save history: {e}")

    def _read_history_file(self, path) -> List[Calculation]:
        """Read the CSV and rebuild Calculations, raising OperationError on any problem."""
        try:
            df = pd.read_csv(path, dtype=str, encoding=self.config.default_encoding)
        except FileNotFoundError:
            raise OperationError(f"No history file found at {path}")
        except pd.errors.EmptyDataError:
            raise OperationError("History file is empty")
        except pd.errors.ParserError as e:
            raise OperationError(f"History file is malformed: {e}")
        except (OSError, UnicodeDecodeError) as e:
            raise OperationError(f"Could not read history file: {e}")

        missing = set(CSV_COLUMNS) - set(df.columns)
        if missing:
            raise OperationError(f"History file is missing columns: {sorted(missing)}")

        return [Calculation.from_dict(row) for row in df.to_dict("records")]

    def load_history(self) -> None:
        #reads history from file and loads it into current history
        try:
            loaded = self._read_history_file(self.config.history_file)
        except OperationError as e:
            self.logger.error("Failed to load history: %s", e)
            raise

        self._push_undo()            # loading can be undone
        self.redo_stack.clear()
        self.history = loaded
        self.logger.info("Loaded %d calculations", len(loaded))