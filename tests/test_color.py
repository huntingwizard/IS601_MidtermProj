"""Tests for colors.py: each helper keeps the text and adds the right color code."""

import pytest
from colorama import Fore, Style

from app.colors import error, info, prompt, success, warning


class TestColorHelpers:
    """success, error, warning, and info each wrap text in one color."""

    @pytest.mark.parametrize("helper, color", [
        (success, Fore.GREEN),
        (error, Fore.RED),
        (warning, Fore.YELLOW),
        (info, Fore.CYAN),
    ])
    def test_adds_color_before_text(self, helper, color):
        """The result is exactly: color code + the original text."""
        assert helper("hello") == f"{color}hello"

    @pytest.mark.parametrize("helper", [success, error, warning, info])
    def test_text_is_never_changed(self, helper):
        """Empty text, spaces, and newlines pass through untouched."""
        assert helper("").endswith("")
        assert helper("\nResult: 5  ").endswith("\nResult: 5  ")

    def test_each_helper_uses_a_different_color(self):
        """If two helpers shared a color, the scheme would lose its meaning."""
        codes = {helper("x") for helper in (success, error, warning, info)}
        assert len(codes) == 4


class TestPrompt:
    """prompt makes the input prompt bright so typed text stands out."""

    def test_adds_bright_style(self):
        assert prompt("Enter command: ") == f"{Style.BRIGHT}Enter command: "