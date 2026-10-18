########################
# Calculator Config    #
########################

from dataclasses import dataclass
from decimal import Decimal
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

