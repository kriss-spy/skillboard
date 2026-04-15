"""Tests for skillboard."""

from pathlib import Path

import pytest

from skillboard.config import Config, SkillPaths, get_config, reset_config
from skillboard.manager import Skill, SkillManager


class TestSkill:
    """Tests for Skill dataclass."""

    def test_skill_str_disabled(self):
        """Test string representation of disabled skill."""
        skill = Skill(name="test-skill", path=Path("/tmp/test"))
        assert str(skill) == "✗ test-skill"

    def test_skill_str_enabled(self):
        """Test string representation of enabled skill."""
        skill = Skill(name="test-skill", path=Path("/tmp/test"), is_enabled=True)
        assert str(skill) == "✓ test-skill"

    def test_skill_str_symlink(self):
        """Test string representation of symlinked skill."""
        skill = Skill(name="test-skill", path=Path("/tmp/test"), is_enabled=True, is_symlink=True)
        assert str(skill) == "✓ test-skill (link)"


class TestSkillManager:
    """Tests for SkillManager."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary source and target directories."""
        source = tmp_path / "warehouse"
        target = tmp_path / "active"
        source.mkdir()
        target.mkdir()
        return source, target

    def test_init_creates_directories(self, tmp_path):
        """Test that initialization creates directories."""
        source = tmp_path / "new_source"
        target = tmp_path / "new_target"

        assert not source.exists()
        assert not target.exists()

        SkillManager(source, target)

        assert source.exists()
        assert target.exists()

    def test_scan_skills_empty(self, temp_dirs):
        """Test scanning empty directories."""
        source, target = temp_dirs
        manager = SkillManager(source, target)

        skills = manager.scan_skills()
        assert skills == []

    def test_scan_skills_from_source(self, temp_dirs):
        """Test scanning skills from source only."""
        source, target = temp_dirs

        # Create test skills
        (source / "skill-a").mkdir()
        (source / "skill-b").mkdir()

        manager = SkillManager(source, target)
        skills = manager.scan_skills()

        assert len(skills) == 2
        assert all(not s.is_enabled for s in skills)
        assert {s.name for s in skills} == {"skill-a", "skill-b"}

    def test_scan_skills_ignores_hidden(self, temp_dirs):
        """Test that hidden directories are ignored."""
        source, target = temp_dirs

        (source / "skill-a").mkdir()
        (source / ".hidden").mkdir()

        manager = SkillManager(source, target)
        skills = manager.scan_skills()

        assert len(skills) == 1
        assert skills[0].name == "skill-a"

    def test_enable_skill(self, temp_dirs):
        """Test enabling a skill."""
        source, target = temp_dirs

        (source / "test-skill").mkdir()

        manager = SkillManager(source, target)
        result = manager.enable_skill("test-skill")

        assert result is True
        assert (target / "test-skill").exists()
        assert (target / "test-skill").is_symlink()

    def test_enable_skill_missing(self, temp_dirs):
        """Test enabling a non-existent skill."""
        source, target = temp_dirs

        manager = SkillManager(source, target)
        result = manager.enable_skill("missing-skill")

        assert result is False

    def test_disable_skill(self, temp_dirs):
        """Test disabling a skill."""
        source, target = temp_dirs

        (source / "test-skill").mkdir()

        manager = SkillManager(source, target)
        manager.enable_skill("test-skill")

        result = manager.disable_skill("test-skill")

        assert result is True
        assert not (target / "test-skill").exists()

    def test_apply_changes(self, temp_dirs):
        """Test applying multiple changes."""
        source, target = temp_dirs

        (source / "skill-a").mkdir()
        (source / "skill-b").mkdir()

        manager = SkillManager(source, target)

        # Enable skill-a only
        enabled, disabled = manager.apply_changes({"skill-a"})

        assert enabled == ["skill-a"]
        assert disabled == []
        assert (target / "skill-a").exists()
        assert not (target / "skill-b").exists()

    def test_apply_changes_disable(self, temp_dirs):
        """Test disabling skills via apply_changes."""
        source, target = temp_dirs

        (source / "skill-a").mkdir()
        (source / "skill-b").mkdir()

        manager = SkillManager(source, target)
        manager.enable_skill("skill-a")
        manager.enable_skill("skill-b")

        # Disable skill-a
        enabled, disabled = manager.apply_changes({"skill-b"})

        assert enabled == []
        assert disabled == ["skill-a"]
        assert not (target / "skill-a").exists()
        assert (target / "skill-b").exists()


class TestSkillPaths:
    """Tests for SkillPaths configuration."""

    def test_get_path_known(self):
        """Test getting known paths."""
        paths = SkillPaths()

        assert paths.get_path("warehouse") == paths.warehouse
        assert paths.get_path("claude") == paths.claude

    def test_get_path_unknown(self):
        """Test getting unknown path raises error."""
        paths = SkillPaths()

        with pytest.raises(ValueError, match="Unknown skill path"):
            paths.get_path("unknown")

    def test_list_paths(self):
        """Test listing all paths."""
        paths = SkillPaths()
        all_paths = paths.list_paths()

        assert "warehouse" in all_paths
        assert "claude" in all_paths
        assert "agent" in all_paths


class TestConfig:
    """Tests for Config class."""

    def test_config_has_paths(self):
        """Test that config has paths attribute."""
        config = Config()
        assert hasattr(config, "paths")
        assert isinstance(config.paths, SkillPaths)

    def test_get_config_singleton(self):
        """Test that get_config returns same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_reset_config(self):
        """Test that reset_config creates new instance."""
        config1 = get_config()
        reset_config()
        config2 = get_config()

        assert config1 is not config2
