"""Tests for error handling module."""

import sys
from io import StringIO

import pytest

from skillboard.errors import ExitCode, cancel, error, info, success, warning


class TestError:
    """Tests for error() function."""

    def test_error_default_code(self, capsys):
        """Test error() with default exit code."""
        with pytest.raises(SystemExit) as exc_info:
            error("Test error message")
        assert exc_info.value.code == ExitCode.OPERATION_FAILED

    def test_error_custom_code(self, capsys):
        """Test error() with custom exit code."""
        with pytest.raises(SystemExit) as exc_info:
            error("Test error message", ExitCode.INVALID_ARGUMENTS)
        assert exc_info.value.code == ExitCode.INVALID_ARGUMENTS


class TestCancel:
    """Tests for cancel() function."""

    def test_cancel_default_message(self):
        """Test cancel() with default message."""
        with pytest.raises(SystemExit) as exc_info:
            cancel()
        assert exc_info.value.code == ExitCode.CANCELLED_BY_USER

    def test_cancel_custom_message(self):
        """Test cancel() with custom message."""
        with pytest.raises(SystemExit) as exc_info:
            cancel("Custom cancel message")
        assert exc_info.value.code == ExitCode.CANCELLED_BY_USER


class TestWarning:
    """Tests for warning() function."""

    def test_warning_output(self):
        """Test warning() prints message."""
        # warning() doesn't exit, just prints
        warning("Test warning")


class TestInfo:
    """Tests for info() function."""

    def test_info_output(self):
        """Test info() prints message."""
        # info() doesn't exit, just prints
        info("Test info")


class TestSuccess:
    """Tests for success() function."""

    def test_success_output(self):
        """Test success() prints message."""
        # success() doesn't exit, just prints
        success("Test success")


class TestExitCodes:
    """Tests for ExitCode enum values."""

    def test_exit_code_values(self):
        """Test all exit code values are correct."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.INVALID_ARGUMENTS == 1
        assert ExitCode.SOURCE_NOT_FOUND == 2
        assert ExitCode.TARGET_NOT_FOUND == 3
        assert ExitCode.PERMISSION_DENIED == 4
        assert ExitCode.OPERATION_FAILED == 5
        assert ExitCode.MISSING_DEPENDENCY == 6
        assert ExitCode.CANCELLED_BY_USER == 7

    def test_exit_code_uniqueness(self):
        """Test all exit codes are unique."""
        codes = list(ExitCode)
        values = [code.value for code in codes]
        assert len(values) == len(set(values)), "Exit codes should be unique"
