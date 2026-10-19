"""
Shared pytest fixtures.

Pytest loads this file automatically, so every test file in tests/ can use
these fixtures just by naming them as test parameters.
"""

import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.operations import OperationFactory

# Every environment variable the app reads. They are cleared before each test.
ENV_KEYS = [
    "CALCULATOR_BASE_DIR", "CALCULATOR_LOG_DIR", "CALCULATOR_LOG_FILE",
    "CALCULATOR_HISTORY_DIR", "CALCULATOR_HISTORY_FILE",
    "CALCULATOR_MAX_HISTORY_SIZE", "CALCULATOR_AUTO_SAVE", "CALCULATOR_PRECISION",
    "CALCULATOR_MAX_INPUT_VALUE", "CALCULATOR_DEFAULT_ENCODING",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """
    Remove CALCULATOR_* variables before every test (autouse = runs automatically).

    load_dotenv() copies your real .env into the environment when the app is
    imported. Without this, a test could write to your real logs/ and history/
    folders or fail because of your personal settings.
    """
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def config(tmp_path):
    """A config whose logs and history live in a temporary folder pytest deletes later."""
    return CalculatorConfig(base_dir=tmp_path)


@pytest.fixture
def calc(config):
    """A fresh Calculator that uses the temporary config."""
    return Calculator(config)


@pytest.fixture
def run(calc):
    """Shortcut: run('add', '2', '3') picks the operation and performs it in one call."""
    def _run(op, a, b):
        calc.set_operation(OperationFactory.create_operation(op))
        return calc.perform_operation(a, b)
    return _run