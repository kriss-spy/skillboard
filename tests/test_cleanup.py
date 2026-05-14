"""Tests for cleanup command and orphaned skill detection."""

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from skillboard.cli import cli
from skillboard.manager import SkillManager


class TestFindOrphanedSkills:
    """Tests for find_orphaned_skills method."""

    def test_no_orphaned_skills(self, tmp_path):
        """Test with no orphaned skills."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        # Create a valid skill and symlink it
        (source / "valid-skill").mkdir()
        (target / "valid-skill").symlink_to(source / "valid-skill", target_is_directory=True)

        manager = SkillManager(source, target)
        orphaned = manager.find_orphaned_skills()

        assert len(orphaned) == 0

    def test_orphaned_symlink(self, tmp_path):
        """Test detecting an orphaned symlink."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        # Create a skill, symlink it, then delete the source
        (source / "orphan-skill").mkdir()
        (target / "orphan-skill").symlink_to(source / "orphan-skill", target_is_directory=True)
        shutil.rmtree(source / "orphan-skill")

        manager = SkillManager(source, target)
        orphaned = manager.find_orphaned_skills()

        assert len(orphaned) == 1
        assert orphaned[0].name == "orphan-skill"

    def test_broken_symlink(self, tmp_path):
        """Test detecting a broken symlink (points to never-existing path)."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        # Create a symlink to a non-existent path
        (target / "broken-skill").symlink_to(
            tmp_path / "nonexistent" / "skill", target_is_directory=True
        )

        manager = SkillManager(source, target)
        orphaned = manager.find_orphaned_skills()

        assert len(orphaned) == 1
        assert orphaned[0].name == "broken-skill"

    def test_ignores_regular_directories(self, tmp_path):
        """Test that regular directories are not flagged as orphaned."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        # Create a regular directory in target (not a symlink)
        (target / "regular-dir").mkdir()

        manager = SkillManager(source, target)
        orphaned = manager.find_orphaned_skills()

        assert len(orphaned) == 0

    def test_ignores_hidden_files(self, tmp_path):
        """Test that hidden items are ignored."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        # Create a hidden symlink
        (target / ".hidden-skill").symlink_to(
            tmp_path / "nonexistent", target_is_directory=True
        )

        manager = SkillManager(source, target)
        orphaned = manager.find_orphaned_skills()

        assert len(orphaned) == 0

    def test_empty_target(self, tmp_path):
        """Test with empty target directory."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        manager = SkillManager(source, target)
        orphaned = manager.find_orphaned_skills()

        assert len(orphaned) == 0

    def test_multiple_orphaned_skills(self, tmp_path):
        """Test detecting multiple orphaned skills."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        # Create multiple skills, symlink them, delete sources
        for name in ["skill-a", "skill-b", "skill-c"]:
            (source / name).mkdir()
            (target / name).symlink_to(source / name, target_is_directory=True)
            shutil.rmtree(source / name)

        manager = SkillManager(source, target)
        orphaned = manager.find_orphaned_skills()

        assert len(orphaned) == 3
        assert {s.name for s in orphaned} == {"skill-a", "skill-b", "skill-c"}


class TestRemoveOrphanedSkill:
    """Tests for remove_orphaned_skill method."""

    def test_remove_orphaned_symlink(self, tmp_path):
        """Test removing an orphaned symlink."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        (source / "orphan").mkdir()
        (target / "orphan").symlink_to(source / "orphan", target_is_directory=True)
        shutil.rmtree(source / "orphan")

        manager = SkillManager(source, target)
        result = manager.remove_orphaned_skill("orphan")

        assert result is True
        assert not (target / "orphan").exists()

    def test_remove_already_gone(self, tmp_path):
        """Test removing a skill that doesn't exist."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        manager = SkillManager(source, target)
        result = manager.remove_orphaned_skill("nonexistent")

        assert result is True

    def test_remove_regular_directory(self, tmp_path):
        """Test that regular directories are not removed."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()

        (target / "regular").mkdir()

        manager = SkillManager(source, target)
        result = manager.remove_orphaned_skill("regular")

        assert result is False
        assert (target / "regular").exists()


class TestCleanupCommand:
    """Tests for cleanup CLI command."""

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

        # Patch both modules since cli imports get_config
        monkeypatch.setattr("skillboard.config.get_config", mock_get_config)
        monkeypatch.setattr("skillboard.cli.get_config", mock_get_config)

    def test_cleanup_no_orphaned(self, tmp_path, monkeypatch):
        """Test cleanup with no orphaned skills."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        # Create a valid symlink
        (warehouse / "valid").mkdir()
        (agent / "valid").symlink_to(warehouse / "valid", target_is_directory=True)

        self._mock_config(monkeypatch, warehouse, agent)

        result = runner.invoke(cli, ["cleanup", "--all"])
        assert result.exit_code == 0
        assert "No orphaned skills" in result.output

    def test_cleanup_dry_run(self, tmp_path, monkeypatch):
        """Test cleanup --dry-run."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        # Create orphaned symlink
        (warehouse / "orphan").mkdir()
        (agent / "orphan").symlink_to(warehouse / "orphan", target_is_directory=True)
        shutil.rmtree(warehouse / "orphan")

        self._mock_config(monkeypatch, warehouse, agent)

        result = runner.invoke(cli, ["cleanup", "--dry-run"])
        assert result.exit_code == 0
        assert "orphan" in result.output
        assert "No changes made" in result.output
        # Symlink should still exist (broken symlink)
        assert (agent / "orphan").is_symlink()

    def test_cleanup_all(self, tmp_path, monkeypatch):
        """Test cleanup --all removes orphaned skills."""
        runner = CliRunner()

        warehouse = tmp_path / "warehouse"
        agent = tmp_path / "agent"
        warehouse.mkdir()
        agent.mkdir()

        # Create orphaned symlink
        (warehouse / "orphan").mkdir()
        (agent / "orphan").symlink_to(warehouse / "orphan", target_is_directory=True)
        shutil.rmtree(warehouse / "orphan")

        self._mock_config(monkeypatch, warehouse, agent)

        result = runner.invoke(cli, ["cleanup", "--all"])
        assert result.exit_code == 0
        assert "1 removed" in result.output or "Removed:" in result.output
        # Symlink should be gone
        assert not (agent / "orphan").exists()

    def test_cleanup_unknown_agent(self, tmp_path, monkeypatch):
        """Test cleanup with unknown agent."""
        runner = CliRunner()

        result = runner.invoke(cli, ["cleanup", "unknown-agent"])
        assert result.exit_code == 0
        assert "Unknown agent" in result.output

    def test_cleanup_nonexistent_directory(self, tmp_path, monkeypatch):
        """Test cleanup with non-existent directory."""
        runner = CliRunner()

        result = runner.invoke(cli, ["cleanup", "claude", "--scope", "local"])
        assert result.exit_code == 0
        assert (
            "Directory does not exist" in result.output
            or "No orphaned skills" in result.output
        )
