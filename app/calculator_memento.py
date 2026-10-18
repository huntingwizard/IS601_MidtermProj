from dataclasses import dataclass, field
import datetime
from typing import Tuple

from app.calculation import Calculation


@dataclass(frozen=True)
class CalculatorMemento:
    """Immutable snapshot of the calculator's history at one moment."""
    history: Tuple[Calculation, ...]
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)