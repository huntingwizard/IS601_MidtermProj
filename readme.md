# Advanced Calculator

A command-line calculator built in Python. It supports ten arithmetic operations, undo/redo, automatic history saving to CSV, file logging, configurable settings, and color-coded output.

The project demonstrates several design patterns (Factory, Memento, Observer), custom exception handling, `pandas` CSV persistence, automated tests with `pytest`, and a GitHub Actions CI pipeline.

## Table of Contents

1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Program](#running-the-program)
6. [Usage Guide](#usage-guide)
7. [Design Patterns](#design-patterns)
8. [Logging](#logging)
9. [Error Handling](#error-handling)
10. [Testing](#testing)
11. [CI/CD](#cicd)

## Features

- **Ten operations:** add, subtract, multiply, divide, power, root, modulus, integer division, percentage, absolute difference
- **Exact decimal math** using Python's `Decimal`, so `0.1 + 0.2` is `0.3`
- **Undo and redo** of calculations, history clearing, and history loading
- **Auto-save** of history to a CSV file after every calculation, plus manual `save` and `load` (using `pandas`)
- **Logging** of calculations, warnings, and errors to a log file
- **Configuration** through a `.env` file, with defaults for every setting
- **Input validation** with clear error messages; the app never crashes on bad input
- **Color-coded output** (Colorama): green for results, red for errors, yellow for warnings, cyan for information

## Project Structure

```
project_root/
├── app/
│   ├── __init__.py
│   ├── calculation.py          # Calculation value object (operation, operands, result, timestamp)
│   ├── calculator.py           # Calculator: history, undo/redo, observers, CSV save/load
│   ├── calculator_config.py    # Loads and validates settings from .env
│   ├── calculator_memento.py   # Memento: immutable snapshot of history for undo/redo
│   ├── calculator_repl.py      # Command-line interface (REPL)
│   ├── colors.py               # Color helpers (Colorama)
│   ├── exceptions.py           # Custom exceptions
│   ├── history.py              # Observers: LoggingObserver, AutoSaveObserver
│   ├── input_validators.py     # Number parsing and range checks
│   ├── logger.py               # Logging setup
│   └── operations.py           # Operation classes and OperationFactory
├── tests/                      # pytest test suite
├── .github/workflows/python-app.yml
├── .env                        # Your local settings (not committed)
├── main.py                     # Entry point
├── requirements.txt
└── README.md
```

## Installation

**Requirements:** Python 3.9 or newer and Git.

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd <project-folder>
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Main dependencies: `pandas`, `python-dotenv`, `colorama`, `pytest`, `pytest-cov`.

## Configuration

Settings are read from a `.env` file in the project root using `python-dotenv`. **Every setting is optional.** If a variable is missing, the default is used.

Create a `.env` file:

```env
CALCULATOR_LOG_DIR=logs
CALCULATOR_HISTORY_DIR=history
CALCULATOR_MAX_HISTORY_SIZE=1000
CALCULATOR_AUTO_SAVE=true
CALCULATOR_PRECISION=10
CALCULATOR_MAX_INPUT_VALUE=1e999
CALCULATOR_DEFAULT_ENCODING=utf-8
```

| Variable | Description | Default |
|---|---|---|
| `CALCULATOR_BASE_DIR` | Folder that logs and history are stored under | Project root |
| `CALCULATOR_LOG_DIR` | Directory for log files | `<base>/logs` |
| `CALCULATOR_LOG_FILE` | Full path of the log file | `<log dir>/calculator.log` |
| `CALCULATOR_HISTORY_DIR` | Directory for history files | `<base>/history` |
| `CALCULATOR_HISTORY_FILE` | Full path of the history CSV | `<history dir>/calculator_history.csv` |
| `CALCULATOR_MAX_HISTORY_SIZE` | Maximum number of history entries kept (oldest dropped first) | `1000` |
| `CALCULATOR_AUTO_SAVE` | Save history after each calculation (`true` or `false`) | `true` |
| `CALCULATOR_PRECISION` | Decimal places shown in results | `10` |
| `CALCULATOR_MAX_INPUT_VALUE` | Largest absolute value a user may enter | `1e999` |
| `CALCULATOR_DEFAULT_ENCODING` | Encoding for file reading and writing | `utf-8` |

**Validation on startup:**
- History size, precision, and maximum input must be greater than zero.
- Numeric settings that can't be parsed (for example `CALCULATOR_PRECISION=abc`) raise a `ConfigurationError` that names the bad variable.
- The encoding must be a real encoding name.
- Only `true` or `1` turns auto-save on; any other value turns it off.

**Precision note:** `CALCULATOR_PRECISION` controls how many decimal places are *displayed*. Stored results keep full precision.

## Running the Program

```bash
python3 main.py
```

You'll see a prompt:

```
Calculator started. Type 'help' for commands.
Enter command:
```

## Usage Guide

### Performing a calculation

Type an operation name. The calculator then asks for two numbers:

```
Enter command: add

 enter your 2 number inputs
First Input 2
Second input 3

Result: 5
```

### Operations

| Command | Calculates | Example (a, b) | Result |
|---|---|---|---|
| `add` | a + b | 2, 3 | 5 |
| `subtract` | a − b | 2, 3 | -1 |
| `multiply` | a × b | 4, 2.5 | 10 |
| `divide` | a ÷ b | 7, 2 | 3.5 |
| `power` | a raised to b | 2, 3 | 8 |
| `root` | b-th root of a (a^(1/b)) | 27, 3 | 3 |
| `modulus` | remainder of a ÷ b | 7, 3 | 1 |
| `int_divide` | a ÷ b with the fraction cut off | 7, 2 | 3 |
| `percent` | (a ÷ b) × 100 | 50, 200 | 25 |
| `abs_diff` | \|a − b\| | 3, 10 | 7 |

Behavior details:
- **`int_divide`** truncates toward zero (it does not round or floor), so `-7 int_divide 2` is `-3`.
- **`modulus`** takes the sign of the first number, so `-7 modulus 3` is `-1`.
- **`power`** accepts negative exponents (`5 ** -1 = 0.2`).
- **`root`** accepts a negative degree (`8` with `-3` gives `0.5`).

### Other commands

| Command | Description |
|---|---|
| `history` | Show all calculations in the current session |
| `undo` | Undo the last calculation (or the last `clear` or `load`) |
| `redo` | Redo the last undone action |
| `clear` | Clear the history (can be undone) |
| `save` | Save the history to the CSV file |
| `load` | Load the history from the CSV file (can be undone) |
| `help` | Show the list of commands |
| `exit` | Exit the program |

### Example session

```
Enter command: add
First Input 2
Second input 3
Result: 5

Enter command: percent
First Input 5
Second input 10
Result: 50

Enter command: history
1. Addition(2, 3) = 5
2. Percent(5, 10) = 50

Enter command: undo
Operation undone

Enter command: redo
Operation redone
```

### Invalid input

Errors are shown in red and the program keeps running:

| Input | Message |
|---|---|
| `abc` as a number | `Error: Invalid number format: abc` |
| `divide` by 0 | `Error: Division by zero is not allowed` |
| `root` of a negative number | `Error: Cannot calculate root of negative number` |
| `power` 0 to a negative exponent | `Error: 0 cannot be raised to negative power` |
| Number above the maximum | `Error: Value exceeds maximum allowed: ...` |
| `load` with no saved file | `Error: ... No history file found ...` |

### History file

History is saved as CSV with these columns:

```
operation,operand1,operand2,result,timestamp
```

Numbers are written as text and read back as text, so values like `0.1` keep their exact precision. A missing, empty, malformed, or incomplete file produces a clear error message instead of a crash.

**Auto-save:** with `CALCULATOR_AUTO_SAVE=true`, the file is rewritten with the full history after every successful calculation, so it always matches what is in memory.

### Color scheme

| Color | Used for |
|---|---|
| Green | Results and confirmations (saved, loaded, cleared, undone, redone) |
| Red | Errors |
| Yellow | Warnings (nothing to undo, empty history, unknown command, cancelled) |
| Cyan | Help text, history entries, and general information |

## Design Patterns

- **Factory (`operations.py`):** `OperationFactory` creates operation objects from command names (`'add'` → `Addition`). Adding an operation means writing one class and registering one name.
- **Memento (`calculator_memento.py`, `calculator.py`):** before each change, the calculator saves an immutable snapshot of the history. `undo` and `redo` move snapshots between two stacks. Snapshots are a frozen dataclass holding a tuple, so a saved state can't be changed by accident.
- **Observer (`history.py`):** observers are registered with the calculator and notified after each successful calculation.
  - `LoggingObserver` logs the operation, operands, and result.
  - `AutoSaveObserver` saves the current history to CSV when auto-save is on.
  - A failing observer is logged and skipped, so it can't break the calculation or other observers.
- **Strategy:** the calculator holds the current `Operation` object and runs it.

## Logging

Logs are written to the file set by `CALCULATOR_LOG_FILE` (default `logs/calculator.log`) in the format:

```
2026-10-18 14:02:11,123 - INFO - Calculation: Addition(2, 3) = 5
```

| Level | Used for |
|---|---|
| INFO | Successful calculations, undo/redo, clear, save, load, auto-save, observers added or removed |
| WARNING | Invalid user input, undo or redo with nothing to undo or redo |
| ERROR | Failed operations, failed saves and loads, observer failures |

Log messages go to the file only, not to the terminal. To follow the log while using the calculator:

```bash
tail -f logs/calculator.log
```

## Error Handling

Custom exceptions live in `app/exceptions.py`:

| Exception | Raised when |
|---|---|
| `CalculatorError` | Base class for all errors below |
| `ValidationError` | Input is not a valid number, is too large, or breaks an operation's rules (like dividing by zero) |
| `OperationError` | A calculation fails, an operation is unknown, or CSV saving and loading fails |
| `ConfigurationError` | A `.env` setting is invalid |

The REPL catches these and prints a friendly message. `Ctrl+C` cancels the current command, and `Ctrl+D` exits cleanly.

## Testing

Run the whole suite:

```bash
pytest
```

Run with coverage (the project requires at least 90%):

```bash
pytest --cov=app --cov-report=term-missing
```

The `Missing` column in the report lists any lines no test reaches. To enforce the threshold the same way CI does:

```bash
pytest --cov=app --cov-fail-under=90
```

Run one file or one test:

```bash
pytest tests/test_operations.py -v
pytest tests/test_calculator.py::test_undo_and_redo
```

Tests use a temporary folder for logs and history, and clear any `CALCULATOR_*` variables first (see `tests/conftest.py`), so running them never touches your real `logs/`, `history/`, or `.env`.

| Test file | Covers |
|---|---|
| `test_operations.py` | Every operation (valid and invalid inputs) and the factory |
| `test_calculation.py` | The `Calculation` object, serialization, formatting |
| `test_input_validators.py` | Number parsing and range checks |
| `test_calculator_config.py` | Defaults, `.env` overrides, and validation |
| `test_calculator.py` | Calculator logic, undo/redo, CSV save and load |
| `test_calculator_memento.py` | Memento snapshots and restoring |
| `test_history.py` | Observers and notifications |
| `test_logger.py` | Log file setup and output |
| `test_colors.py` | Color helpers |
| `test_calculator_repl.py` | The command-line interface, using scripted input |

## CI/CD

A GitHub Actions workflow in `.github/workflows/python-app.yml` runs on every push and pull request to `main`. It:

1. Checks out the code
2. Sets up Python
3. Installs the packages in `requirements.txt`
4. Runs `pytest --cov=app --cov-fail-under=90`

The pipeline fails if any test fails or coverage drops below 90%, so broken code can't be merged unnoticed.