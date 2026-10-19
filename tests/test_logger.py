"""
Tests for logger.py.

The logger writes to a file and doesn't propagate to the terminal, so pytest's
caplog can't see its messages. These tests read the log file instead.
"""

import logging

from app.calculator_config import CalculatorConfig
from app.logger import LOGGER_NAME, get_logger, setup_logging


def read_log(config: CalculatorConfig) -> str:
    """Flush the handlers, then return the whole log file as text."""
    for handler in get_logger().handlers:
        handler.flush()
    return config.log_file.read_text(encoding=config.default_encoding)


class TestSetupLogging:
    """setup_logging builds the calculator logger from the config."""

    def test_returns_named_logger(self, config):
        logger = setup_logging(config)
        assert logger.name == LOGGER_NAME
        assert logger is get_logger()

    def test_creates_log_folder_and_file(self, config):
        """The log folder doesn't exist yet; setup creates it along with the file."""
        assert not config.log_dir.exists()
        setup_logging(config)
        assert config.log_file.exists()

    def test_level_is_info(self, config):
        assert setup_logging(config).level == logging.INFO

    def test_does_not_propagate(self, config):
        """Messages go to the file only, not to the terminal."""
        assert setup_logging(config).propagate is False

    def test_calling_twice_keeps_one_handler(self, config):
        """A second call replaces the handler, so lines are never duplicated."""
        setup_logging(config)
        logger = setup_logging(config)
        assert len(logger.handlers) == 1
        logger.info("written-once")
        assert read_log(config).count("written-once") == 1


class TestLogOutput:
    """What actually ends up in the file."""

    def test_format_has_time_level_and_message(self, config):
        logger = setup_logging(config)
        logger.info("format check")
        line = read_log(config).strip()
        # Format is: timestamp - LEVEL - message
        assert line.endswith("- INFO - format check")
        assert line[:4].isdigit()          # starts with the year

    def test_each_level_is_recorded(self, config):
        logger = setup_logging(config)
        logger.info("an info")
        logger.warning("a warning")
        logger.error("an error")
        text = read_log(config)
        assert "INFO - an info" in text
        assert "WARNING - a warning" in text
        assert "ERROR - an error" in text

    def test_debug_is_ignored(self, config):
        """The level is INFO, so DEBUG messages are filtered out."""
        setup_logging(config).debug("too detailed")
        assert "too detailed" not in read_log(config)


class TestGetLogger:
    """get_logger returns the same shared logger from anywhere."""

    def test_same_object_every_time(self, config):
        setup_logging(config)
        assert get_logger() is get_logger()

    def test_writes_to_configured_file(self, config):
        """A module that only calls get_logger() still logs to the config's file."""
        setup_logging(config)
        get_logger().info("from another module")
        assert "from another module" in read_log(config)