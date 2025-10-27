"""
Colored print utilities for console output
"""

import sys


class Colors:
    """ANSI color codes"""
    # Text colors
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    # Styles
    BOLD = "\033[1m"
    RESET = "\033[0m"


def supports_color():
    """Check if terminal supports color"""
    return sys.stdout.isatty()


def colored_print(message: str, color: str = Colors.WHITE, bold: bool = False, file=sys.stdout):
    """Print colored message if terminal supports it"""
    if supports_color():
        style = Colors.BOLD if bold else ""
        print(f"{style}{color}{message}{Colors.RESET}", file=file)
    else:
        print(message, file=file)


def print_info(message: str):
    """Print info message in green"""
    colored_print(message, Colors.GREEN)


def print_warning(message: str):
    """Print warning message in yellow"""
    colored_print(message, Colors.YELLOW)


def print_error(message: str):
    """Print error message in red"""
    colored_print(message, Colors.RED, file=sys.stderr)


def print_step(message: str):
    """Print step message in cyan bold"""
    colored_print(message, Colors.CYAN, bold=True)


def print_success(message: str):
    """Print success message in green bold"""
    colored_print(f"✅ {message}", Colors.GREEN, bold=True)


def print_failure(message: str):
    """Print failure message in red bold"""
    colored_print(f"❌ {message}", Colors.RED, bold=True)
