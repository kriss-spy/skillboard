"""Skillboard - A lightweight skill management utility for AI coding agents.

This package provides a simple CLI tool to manage AI coding agent skills
by toggling them between a warehouse (source of truth) and active directories
using symbolic links.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("skillboard")
except PackageNotFoundError:
    # Package is not installed (e.g., running from source)
    __version__ = "unknown"

__author__ = "Skillboard Contributors"
__license__ = "MIT"
__url__ = "https://github.com/kriss-spy/skillboard"
