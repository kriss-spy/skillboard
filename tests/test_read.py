"""Tests for read CLI command."""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from skillboard.cli import cli


class TestReadCommand:
    """Tests for read command."""

    def _mock_config(self, monkeypatch, agent, warehouse=None):
        """Helper to mock config paths in CLI."""
        import skillboard.cli
        import skillboard.config

        original_get_config = skillboard.config.get_config

        def mock_get_config():
            config = original_get_config()
            config.paths.agent = agent
            if warehouse:
                config.paths.warehouse = warehouse
            return config

        monkeypatch.setattr("skillboard.config.get_config", mock_get_config)
        monkeypatch.setattr("skillboard.cli.get_config", mock_get_config)

    def test_read_default_agent(self, tmp_path, monkeypatch):
        """Test reading skill from default agent path."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        # Create a skill with SKILL.md
        skill_dir = agent / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test Skill\n\nThis is a test.")
        (skill_dir / "script.py").write_text("print('hello')")

        self._mock_config(monkeypatch, agent, warehouse)

        result = runner.invoke(cli, ["read", "test-skill"])
        assert result.exit_code == 0
        assert "Test Skill" in result.output
        assert "script.py" in result.output

    def test_read_specific_agent(self, tmp_path, monkeypatch):
        """Test reading skill from specific agent path."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        claude = tmp_path / "claude"
        warehouse.mkdir()
        claude.mkdir()

        skill_dir = claude / "claude-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Claude Skill")

        import skillboard.cli
        import skillboard.config

        original_get_config = skillboard.config.get_config

        def mock_get_config():
            config = original_get_config()
            config.paths.warehouse = warehouse
            config.paths.claude = claude
            return config

        monkeypatch.setattr("skillboard.config.get_config", mock_get_config)
        monkeypatch.setattr("skillboard.cli.get_config", mock_get_config)

        result = runner.invoke(cli, ["read", "claude-skill", "-a", "claude"])
        assert result.exit_code == 0
        assert "Claude Skill" in result.output

    def test_read_missing_skill(self, tmp_path, monkeypatch):
        """Test reading a non-existent skill."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        self._mock_config(monkeypatch, agent, warehouse)

        result = runner.invoke(cli, ["read", "missing-skill"])
        assert result.exit_code == 0
        assert "Skill not found" in result.output

    def test_read_no_skill_md(self, tmp_path, monkeypatch):
        """Test reading skill without SKILL.md."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        skill_dir = agent / "no-md-skill"
        skill_dir.mkdir()
        (skill_dir / "README.txt").write_text("No markdown here")

        self._mock_config(monkeypatch, agent, warehouse)

        result = runner.invoke(cli, ["read", "no-md-skill"])
        assert result.exit_code == 0
        assert "No SKILL.md found" in result.output
        assert "README.txt" in result.output

    def test_read_truncate_long_skill_md(self, tmp_path, monkeypatch):
        """Test that long SKILL.md is truncated."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        skill_dir = agent / "long-skill"
        skill_dir.mkdir()
        lines = [f"Line {i}" for i in range(100)]
        (skill_dir / "SKILL.md").write_text("\n".join(lines))

        self._mock_config(monkeypatch, agent, warehouse)

        result = runner.invoke(cli, ["read", "long-skill"])
        assert result.exit_code == 0
        assert "truncated" in result.output
        assert "Line 0" in result.output

    def test_read_github_skills(self, tmp_path, monkeypatch):
        """Test reading from .github/skills directory."""
        runner = CliRunner()

        github_skills = tmp_path / ".github" / "skills"
        github_skills.mkdir(parents=True)

        skill_dir = github_skills / "github-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# GitHub Skill")

        # Change to tmp_path so relative .github/skills works
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(cli, ["read", "github-skill", "--github"])
            assert result.exit_code == 0
            assert "GitHub Skill" in result.output
        finally:
            os.chdir(original_cwd)

    def test_read_local_scope(self, tmp_path, monkeypatch):
        """Test reading from local scope."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        warehouse.mkdir()

        # Create local agent directory
        local_agent = tmp_path / ".agents" / "skills"
        local_agent.mkdir(parents=True)

        skill_dir = local_agent / "local-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Local Skill")

        self._mock_config(monkeypatch, warehouse, warehouse)

        # Change to tmp_path so relative paths work
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(cli, ["read", "local-skill", "--scope", "local"])
            assert result.exit_code == 0
            assert "Local Skill" in result.output
        finally:
            os.chdir(original_cwd)

    def test_read_unknown_agent(self, tmp_path, monkeypatch):
        """Test reading with unknown agent."""
        runner = CliRunner()

        result = runner.invoke(cli, ["read", "my-skill", "-a", "unknown"])
        assert result.exit_code == 0
        assert "Unknown agent" in result.output
