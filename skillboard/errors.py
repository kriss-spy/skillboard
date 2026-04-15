"""Error handling utilities for skillboard.

Provides consistent error handling across the CLI with proper exit codes
and user-friendly error messages.
"""

import sys
from enum import IntEnum
from typing import NoReturn

from rich.console import Console

console = Console()


class ExitCode(IntEnum):
    """Standardized exit codes for skillboard."""

    SUCCESS = 0
    INVALID_ARGUMENTS = 1
    SOURCE_NOT_FOUND = 2
    TARGET_NOT_FOUND = 3
    PERMISSION_DENIED = 4
    OPERATION_FAILED = 5
    MISSING_DEPENDENCY = 6
    CANCELLED_BY_USER = 7


def error(message: str, code: ExitCode = ExitCode.OPERATION_FAILED) -> NoReturn:
    """Print an error message and exit with the specified code.

    Args:
        message: Error message to display
        code: Exit code to use
    """
    console.print(f"[red]Error: {message}[/red]")
    sys.exit(code)


def warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Warning message to display
    """
    console.print(f"[yellow]Warning: {message}[/yellow]")


def info(message: str) -> None:
    """Print an info message.

    Args:
        message: Info message to display
    """
    console.print(f"[dim]{message}[/dim]")


def success(message: str) -> None:
    """Print a success message.

    Args:
        message: Success message to display
    """
    console.print(f"[green]{message}[/green]")


def cancel(message: str = "Cancelled.") -> NoReturn:
    """Print a cancellation message and exit with CANCELLED_BY_USER code.

    Args:
        message: Cancellation message to display
    """
    console.print(f"[yellow]{message}[/yellow]")
    sys.exit(ExitCode.CANCELLED_BY_USER)
