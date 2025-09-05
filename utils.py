"""Shared utilities and common functionality for SolarSynkV3."""

from typing import Dict, Any
import json
import logging


class ConsoleColor:
    """ANSI color codes for console output."""

    OKBLUE = "\033[34m"
    OKCYAN = "\033[36m"
    OKGREEN = "\033[32m"
    MAGENTA = "\033[35m"
    WARNING = "\033[33m"
    FAIL = "\033[31m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def load_settings(settings_path: str = '/data/options.json') -> Dict[str, Any]:
    """
    Load settings from JSON file.

    Args:
        settings_path: Path to the settings JSON file

    Returns:
        Dictionary containing loaded settings

    Raises:
        SystemExit: If settings file cannot be loaded
    """
    try:
        with open(settings_path) as options_file:
            return json.load(options_file)
    except Exception as e:
        logging.error(f"Failed to load settings: {e}")
        print(f"{ConsoleColor.FAIL}Error loading settings.json. "
              f"Ensure the file exists and is valid JSON.{ConsoleColor.ENDC}")
        raise SystemExit(1) from e


def print_colored(message: str, color: str = ConsoleColor.ENDC) -> None:
    """
    Print a message with specified color.

    Args:
        message: The message to print
        color: ANSI color code to use
    """
    print(f"{color}{message}{ConsoleColor.ENDC}")


def format_inverter_output(label: str, value: Any) -> str:
    """
    Format inverter data output consistently.

    Args:
        label: The label for the data
        value: The value to display

    Returns:
        Formatted string with consistent coloring
    """
    return f"{label}: {ConsoleColor.OKCYAN}{str(value)}{ConsoleColor.ENDC}"
