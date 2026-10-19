"""
Tests for calculator_config.py.

Settings come from three places, in this order: a constructor argument,
an environment variable (what .env provides), then a built-in default.
Each class below covers one part of that behavior.
"""

from decimal import Decimal

import pytest

from app.calculator_config import CalculatorConfig, get_project_root
from app.exceptions import ConfigurationError


class TestDefaults:
    """With no arguments and no environment variables, defaults are used."""

    def test_default_values(self, tmp_path):
        config = CalculatorConfig(base_dir=tmp_path)
        assert config.max_history_size == 1000
        assert config.precision == 10
        assert config.auto_save is True
        assert config.max_input_value == Decimal("1e999")
        assert config.default_encoding == "utf-8"

    def test_default_paths(self, tmp_path):
        """Logs and history live in folders under base_dir."""
        config = CalculatorConfig(base_dir=tmp_path)
        assert config.log_dir == (tmp_path / "logs").resolve()
        assert config.history_dir == (tmp_path / "history").resolve()
        assert config.log_file == (tmp_path / "logs" / "calculator.log").resolve()
        assert config.history_file == (
            tmp_path / "history" / "calculator_history.csv"
        ).resolve()

    def test_defaults_pass_validation(self, tmp_path):
        CalculatorConfig(base_dir=tmp_path).validate()  # should not raise

    def test_project_root_contains_app_folder(self):
        assert (get_project_root() / "app").is_dir()

    def test_base_dir_from_env(self, monkeypatch, tmp_path):
        """With no base_dir argument, CALCULATOR_BASE_DIR is used."""
        monkeypatch.setenv("CALCULATOR_BASE_DIR", str(tmp_path))
        assert CalculatorConfig().base_dir == tmp_path.resolve()