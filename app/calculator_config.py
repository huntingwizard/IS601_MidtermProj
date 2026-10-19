########################
# Calculator Config    #
########################

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from numbers import Number
from pathlib import Path
import os
from typing import Optional

from dotenv import load_dotenv

from app.exceptions import ConfigurationError

# Read the .env file (if there is one) so its values are available through os.getenv
load_dotenv()


def get_project_root() -> Path:
    """
    Find the top-level folder of the project.

    Starts from this file's location (app/calculator_config.py) and moves up
    two levels, so paths still work no matter where the program is launched from.

    Returns:
        Path: The project root folder.
    """
    return Path(__file__).parent.parent


@dataclass
class CalculatorConfig:
    """
    Holds every setting the calculator needs.

    Covers folder locations, history size, auto-save, precision, the largest
    allowed input, and file encoding. Each setting is chosen in this order:
    1. A value passed directly to the constructor
    2. A value from the environment / .env file
    3. A built-in default
    """
    def _read_env(name: str, default: str, cast):
        """Read an environment variable and convert it, or raise ConfigurationError."""
        raw = os.getenv(name, default)
        try:
            return cast(raw)
        except (ValueError, InvalidOperation):
            raise ConfigurationError(f"{name} has an invalid value: {raw!r}")
        
    def __init__(
        self,
        base_dir: Optional[Path] = None,
        max_history_size: Optional[int] = None,
        auto_save: Optional[bool] = None,
        precision: Optional[int] = None,
        max_input_value: Optional[Number] = None,
        default_encoding: Optional[str] = None
    ):
        """
        Load each setting from the arguments, the environment, or a default.

        Args:
            base_dir: Folder that logs and history are stored under.
                Defaults to CALCULATOR_BASE_DIR, then the project root.
            max_history_size: Most history entries to keep.
                Defaults to CALCULATOR_MAX_HISTORY_SIZE, then 1000.
            auto_save: Whether history is saved automatically after each calculation.
                Defaults to CALCULATOR_AUTO_SAVE, then True.
            precision: Decimal places used for results.
                Defaults to CALCULATOR_PRECISION, then 10.
            max_input_value: Largest absolute value a user may enter.
                Defaults to CALCULATOR_MAX_INPUT_VALUE, then 1e999.
            default_encoding: Text encoding used when reading and writing files.
                Defaults to CALCULATOR_DEFAULT_ENCODING, then utf-8.
        """
        # Use the given folder, else the environment value, else the project root
        project_root = get_project_root()
        self.base_dir = base_dir or Path(
            os.getenv('CALCULATOR_BASE_DIR', str(project_root))
        ).resolve()

        # Cap on how many calculations are remembered
        self.max_history_size = (
            max_history_size if max_history_size is not None
            else self._read_env('CALCULATOR_MAX_HISTORY_SIZE', '1000', int)
        )
        # An explicit argument wins; otherwise "true" or "1" in the environment means on
        auto_save_env = os.getenv('CALCULATOR_AUTO_SAVE', 'true').lower()
        self.auto_save = auto_save if auto_save is not None else (
            auto_save_env == 'true' or auto_save_env == '1'
        )
        # Number of decimal places for results
        self.precision = (
            precision if precision is not None
            else self._read_env('CALCULATOR_PRECISION', '10', int)
        )
        # Largest absolute number the user is allowed to enter
        self.max_input_value = (
            max_input_value if max_input_value is not None
            else self._read_env('CALCULATOR_MAX_INPUT_VALUE', '1e999', Decimal)
        )
        # Encoding used for any file reads and writes
        self.default_encoding = (
            default_encoding if default_encoding is not None
            else os.getenv('CALCULATOR_DEFAULT_ENCODING', 'utf-8')
        )
    @property
    def log_dir(self) -> Path:
        """
        Folder where log files are written.
        Uses CALCULATOR_LOG_DIR if set, otherwise a "logs" folder inside base_dir.
        Returns:
            Path: Absolute path of the log folder.
        """
        return Path(os.getenv(
            'CALCULATOR_LOG_DIR',
            str(self.base_dir / "logs")
        )).resolve()
    @property
    def history_dir(self) -> Path:
        """
        Folder where history files are stored.
        Uses CALCULATOR_HISTORY_DIR if set, otherwise a "history" folder inside base_dir.
        Returns:
            Path: Absolute path of the history folder.
        """
        return Path(os.getenv(
            'CALCULATOR_HISTORY_DIR',
            str(self.base_dir / "history")
        )).resolve()

    @property
    def history_file(self) -> Path:
        """
        CSV file that the calculation history is saved to and loaded from.
        Uses CALCULATOR_HISTORY_FILE if set, otherwise "calculator_history.csv"
        inside the history folder.
        Returns:
            Path: Absolute path of the history file.
        """
        return Path(os.getenv(
            'CALCULATOR_HISTORY_FILE',
            str(self.history_dir / "calculator_history.csv")
        )).resolve()

    @property
    def log_file(self) -> Path:
        """
        File that log messages are written to.
        Uses CALCULATOR_LOG_FILE if set, otherwise "calculator.log" inside
        the log folder.
        Returns:
            Path: Absolute path of the log file.
        """
        return Path(os.getenv(
            'CALCULATOR_LOG_FILE',
            str(self.log_dir / "calculator.log")
        )).resolve()

    def validate(self) -> None:
        """
        Check that the numeric settings make sense.
        History size, precision, and the maximum input must all be greater than zero.
        Raises:
            ConfigurationError: If any of those settings is zero or negative.
        """
        if self.max_history_size <= 0:
            raise ConfigurationError("max_history_size must be positive")
        if self.precision <= 0:
            raise ConfigurationError("precision must be positive")
        if self.max_input_value <= 0:
            raise ConfigurationError("max_input_value must be positive")