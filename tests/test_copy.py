"""Tests for copy CLI command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from skillboard.cli import cli


class TestCopyCommand:
    """Tests for copy command."""

    def _mock_config(self, monkeypatch, warehouse, agent):
        """Helper to mock config paths in CLI."""
        import skillboard.cli
        import skillboard.config

        original_get_config = skillboard.config.get_config

        def mock_get_config():
            config = original_get_config()
            config.paths.warehouse = warehouse
            config.paths.agent = agent
            return config

        monkeypatch.setattr("skillboard.config.get_config", mock_get_config)
        monkeypatch.setattr("skillboard.cli.get_config", mock_get_config)

    def test_copy_all(self, tmp_path, monkeypatch):
        """Test copying all skills with --all flag."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        # Create skills in warehouse
        (warehouse / "skill-a").mkdir()
        (warehouse / "skill-a" / "SKILL.md").write_text("# Skill A")
        (warehouse / "skill-b").mkdir()
        (warehouse / "skill-b" / "SKILL.md").write_text("# Skill B")

        self._mock_config(monkeypatch, warehouse, agent)

        result = runner.invoke(cli, ["copy", "-i", "warehouse", "-o", "agent", "--all"])
        assert result.exit_code == 0
        assert "Copied:" in result.output or "copied" in result.output
        assert (agent / "skill-a").exists()
        assert (agent / "skill-a" / "SKILL.md").exists()
        assert (agent / "skill-b").exists()

    def test_copy_skips_existing(self, tmp_path, monkeypatch):
        """Test that copy skips existing skills."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        # Create skill in both locations
        (warehouse / "existing").mkdir()
        (warehouse / "existing" / "SKILL.md").write_text("# Warehouse")
        (agent / "existing").mkdir()
        (agent / "existing" / "SKILL.md").write_text("# Agent")

        self._mock_config(monkeypatch, warehouse, agent)

        result = runner.invoke(cli, ["copy", "-i", "warehouse", "-o", "agent", "--all"])
        assert result.exit_code == 0
        assert "Skipped (exists)" in result.output or "skipped" in result.output
        # Should not overwrite
        assert (agent / "existing" / "SKILL.md").read_text() == "# Agent"

    def test_copy_empty_source(self, tmp_path, monkeypatch):
        """Test copying from empty source."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        self._mock_config(monkeypatch, warehouse, agent)

        result = runner.invoke(cli, ["copy", "-i", "warehouse", "-o", "agent", "--all"])
        assert result.exit_code == 0
        assert "No skills found" in result.output

    def test_copy_missing_source(self, tmp_path, monkeypatch):
        """Test copying from non-existent source."""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["copy", "-i", "/nonexistent/path", "-o", "agent", "--all"]
        )
        assert (
            result.exit_code != 0
            or "not found" in result.output.lower()
            or "Error" in result.output
        )
