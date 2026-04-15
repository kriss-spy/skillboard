"""Tests for path resolution utilities."""

from pathlib import Path

import pytest

from skillboard.config import SkillPaths
from skillboard.errors import ExitCode
from skillboard.paths import (
    ensure_target_directory,
    resolve_agent_path,
    resolve_link_source,
    resolve_source_path,
    resolve_target_path,
    validate_source_exists,
)


class MockConfig:
    """Mock config object for testing."""

    def __init__(self):
        self.paths = SkillPaths()


class TestResolveAgentPath:
    """Tests for resolve_agent_path function."""

    def test_resolve_known_agent_global(self):
        """Test resolving a known agent with global scope."""
        config = MockConfig()
        result = resolve_agent_path("claude", "global", config)
        assert result == config.paths.claude

    def test_resolve_known_agent_local(self):
        """Test resolving a known agent with local scope."""
        config = MockConfig()
        result = resolve_agent_path("claude", "local", config)
        assert result == Path("./.claude/skills")

    def test_resolve_unknown_agent(self):
        """Test resolving an unknown agent raises error."""
        config = MockConfig()
        with pytest.raises(SystemExit) as exc_info:
            resolve_agent_path("unknown", "global", config)
        assert exc_info.value.code == ExitCode.INVALID_ARGUMENTS


class TestResolveSourcePath:
    """Tests for resolve_source_path function."""

    def test_resolve_with_none(self):
        """Test resolving None raises error."""
        config = MockConfig()
        with pytest.raises(SystemExit) as exc_info:
            resolve_source_path(None, "global", config)
        assert exc_info.value.code == ExitCode.INVALID_ARGUMENTS

    def test_resolve_known_agent(self):
        """Test resolving a known agent name."""
        config = MockConfig()
        result = resolve_source_path("warehouse", "global", config)
        assert result == config.paths.warehouse

    def test_resolve_explicit_path(self):
        """Test resolving an explicit path."""
        config = MockConfig()
        result = resolve_source_path("/custom/path", "global", config)
        assert result == Path("/custom/path")


class TestResolveTargetPath:
    """Tests for resolve_target_path function."""

    def test_resolve_with_none(self):
        """Test resolving None raises error."""
        config = MockConfig()
        with pytest.raises(SystemExit) as exc_info:
            resolve_target_path(None, "global", config)
        assert exc_info.value.code == ExitCode.INVALID_ARGUMENTS

    def test_resolve_known_agent(self):
        """Test resolving a known agent name."""
        config = MockConfig()
        result = resolve_target_path("claude", "global", config)
        assert result == config.paths.claude


class TestValidateSourceExists:
    """Tests for validate_source_exists function."""

    def test_valid_source(self, tmp_path):
        """Test validating an existing source passes."""
        source = tmp_path / "source"
        source.mkdir()
        # Should not raise
        validate_source_exists(source)

    def test_missing_source(self, tmp_path):
        """Test validating a missing source raises error."""
        source = tmp_path / "missing"
        with pytest.raises(SystemExit) as exc_info:
            validate_source_exists(source)
        assert exc_info.value.code == ExitCode.SOURCE_NOT_FOUND


class TestEnsureTargetDirectory:
    """Tests for ensure_target_directory function."""

    def test_create_target(self, tmp_path):
        """Test creating target directory."""
        target = tmp_path / "nested" / "target"
        assert not target.exists()
        ensure_target_directory(target)
        assert target.exists()

    def test_existing_target(self, tmp_path):
        """Test with existing target directory."""
        target = tmp_path / "target"
        target.mkdir()
        # Should not raise
        ensure_target_directory(target)
        assert target.exists()


class TestResolveLinkSource:
    """Tests for resolve_link_source function."""

    def test_default_agent(self):
        """Test defaulting to 'agent' when input is None."""
        config = MockConfig()
        result = resolve_link_source(None, "global", False, config)
        assert result == config.paths.agent

    def test_link_all_global(self):
        """Test --all flag uses global path."""
        config = MockConfig()
        result = resolve_link_source("agent", "local", True, config)
        assert result == config.paths.agent  # Should use global, not local

    def test_unknown_agent_with_link_all(self):
        """Test --all with unknown agent raises error."""
        config = MockConfig()
        with pytest.raises(SystemExit) as exc_info:
            resolve_link_source("unknown", "global", True, config)
        assert exc_info.value.code == ExitCode.INVALID_ARGUMENTS
