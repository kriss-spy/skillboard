"""Tests for remove CLI command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from skillboard.cli import cli


class TestRemoveCommand:
    """Tests for remove command."""

    def _mock_config(self, monkeypatch, agent):
        """Helper to mock config paths in CLI."""
        import skillboard.cli
        import skillboard.config

        original_get_config = skillboard.config.get_config

        def mock_get_config():
            config = original_get_config()
            config.paths.agent = agent
            return config

        monkeypatch.setattr("skillboard.config.get_config", mock_get_config)
        monkeypatch.setattr("skillboard.cli.get_config", mock_get_config)

    def test_remove_all(self, tmp_path, monkeypatch):
        """Test removing all skills with --all flag."""
        runner = CliRunner()

        agent = tmp_path / "agent"
        agent.mkdir()

        # Create skills in target
        (agent / "skill-a").mkdir()
        (agent / "skill-b").mkdir()

        self._mock_config(monkeypatch, agent)

        result = runner.invoke(cli, ["remove", "-o", "agent", "--all"])
        assert result.exit_code == 0
        assert "Removed:" in result.output or "removed" in result.output
        assert not (agent / "skill-a").exists()
        assert not (agent / "skill-b").exists()

    def test_remove_dry_run(self, tmp_path, monkeypatch):
        """Test remove --dry-run."""
        runner = CliRunner()

        agent = tmp_path / "agent"
        agent.mkdir()

        (agent / "skill-a").mkdir()

        self._mock_config(monkeypatch, agent)

        result = runner.invoke(cli, ["remove", "-o", "agent", "--all", "--dry-run"])
        assert result.exit_code == 0
        assert "skill-a" in result.output
        assert "No changes made" in result.output
        # Should still exist
        assert (agent / "skill-a").exists()

    def test_remove_empty_target(self, tmp_path, monkeypatch):
        """Test removing from empty target."""
        runner = CliRunner()

        agent = tmp_path / "agent"
        agent.mkdir()

        self._mock_config(monkeypatch, agent)

        result = runner.invoke(cli, ["remove", "-o", "agent", "--all"])
        assert result.exit_code == 0
        assert "No skills found" in result.output

    def test_remove_nonexistent_directory(self, tmp_path, monkeypatch):
        """Test removing from non-existent directory."""
        runner = CliRunner()

        result = runner.invoke(cli, ["remove", "-o", "claude", "--output-scope", "local"])
        assert result.exit_code == 0
        assert "Directory does not exist" in result.output

    def test_remove_symlink(self, tmp_path, monkeypatch):
        """Test removing a symlinked skill."""
        runner = CliRunner()

        agent = tmp_path / "agent"
        agent.mkdir()

        # Create a symlink skill
        source = tmp_path / "warehouse" / "linked-skill"
        source.mkdir(parents=True)
        (agent / "linked-skill").symlink_to(source, target_is_directory=True)

        self._mock_config(monkeypatch, agent)

        result = runner.invoke(cli, ["remove", "-o", "agent", "--all"])
        assert result.exit_code == 0
        assert "Removed:" in result.output
        assert not (agent / "linked-skill").exists()
        # Source should still exist
        assert source.exists()

    def test_remove_unknown_agent(self, tmp_path, monkeypatch):
        """Test remove with unknown agent/path."""
        runner = CliRunner()

        result = runner.invoke(cli, ["remove", "-o", "unknown-agent"])
        assert result.exit_code == 0
        assert "Directory does not exist" in result.output
