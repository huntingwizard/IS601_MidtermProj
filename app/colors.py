"""
Color helpers for the REPL.

All color choices live here, so changing the look of the app means
editing one file instead of every print statement.
"""

from colorama import Fore, Style, init

# autoreset=True puts the color back to normal after every print, so one
# colored message can never "leak" its color into the next line.
# On Windows, init() also translates the color codes so they display.
init(autoreset=True)


def success(text: str) -> str:
    """Green: a calculation result or a confirmed action."""
    return f"{Fore.GREEN}{text}"


def error(text: str) -> str:
    """Red: something failed (bad input, operation error)."""
    return f"{Fore.RED}{text}"


def warning(text: str) -> str:
    """Yellow: not an error, but nothing happened (e.g. nothing to undo)."""
    return f"{Fore.YELLOW}{text}"


def info(text: str) -> str:
    """Cyan: headings, help text, and general information."""
    return f"{Fore.CYAN}{text}"


def prompt(text: str) -> str:
    """Bright text for input prompts."""
    return f"{Style.BRIGHT}{text}"