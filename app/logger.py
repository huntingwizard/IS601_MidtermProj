import logging
from app.calculator_config import CalculatorConfig

LOGGER_NAME = "calculator"


def setup_logging(config: CalculatorConfig) -> logging.Logger:
    """Send the calculator logger to the configured log file (safe to call repeatedly)."""
    config.log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    for h in logger.handlers[:]:
        h.close()
        logger.removeHandler(h)
    handler = logging.FileHandler(config.log_file, encoding=config.default_encoding)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)