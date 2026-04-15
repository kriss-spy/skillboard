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


class TestContentHash:
    """Tests for content hash functionality."""

    def test_get_skill_content_hash_same_content(self, tmp_path):
        """Test that identical skills have same hash."""
        from skillboard.manager import get_skill_content_hash

        # Create two identical skill directories
        skill1 = tmp_path / "skill1"
        skill2 = tmp_path / "skill2"
        skill1.mkdir()
        skill2.mkdir()

        # Create identical files
        (skill1 / "README.md").write_text("# Test Skill")
        (skill2 / "README.md").write_text("# Test Skill")

        hash1 = get_skill_content_hash(skill1)
        hash2 = get_skill_content_hash(skill2)

        assert hash1 == hash2
        assert hash1 != ""  # Hash should not be empty

    def test_get_skill_content_hash_different_content(self, tmp_path):
        """Test that different skills have different hashes."""
        from skillboard.manager import get_skill_content_hash

        skill1 = tmp_path / "skill1"
        skill2 = tmp_path / "skill2"
        skill1.mkdir()
        skill2.mkdir()

        # Create different files
        (skill1 / "README.md").write_text("# Skill One")
        (skill2 / "README.md").write_text("# Skill Two")

        hash1 = get_skill_content_hash(skill1)
        hash2 = get_skill_content_hash(skill2)

        assert hash1 != hash2

    def test_are_skills_identical(self, tmp_path):
        """Test skill identity check."""
        from skillboard.manager import are_skills_identical

        skill1 = tmp_path / "skill1"
        skill2 = tmp_path / "skill2"
        skill1.mkdir()
        skill2.mkdir()

        (skill1 / "file.txt").write_text("content")
        (skill2 / "file.txt").write_text("content")

        assert are_skills_identical(skill1, skill2) is True

        # Change one file
        (skill2 / "file.txt").write_text("different")
        assert are_skills_identical(skill1, skill2) is False


class TestSkillCounting:
    """Tests for skill counting functionality."""

    def test_count_skills_in_directory(self, tmp_path):
        """Test counting skills in a directory."""
        from skillboard.manager import count_skills_in_directory

        # Empty directory
        assert count_skills_in_directory(tmp_path) == 0

        # Add skills
        (tmp_path / "skill-a").mkdir()
        (tmp_path / "skill-b").mkdir()
        assert count_skills_in_directory(tmp_path) == 2

    def test_count_skills_ignores_hidden(self, tmp_path):
        """Test that hidden directories are ignored."""
        from skillboard.manager import count_skills_in_directory

        (tmp_path / "skill-a").mkdir()
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "__pycache__").mkdir()

        assert count_skills_in_directory(tmp_path) == 1

    def test_count_skills_nonexistent_path(self, tmp_path):
        """Test counting in non-existent path."""
        from skillboard.manager import count_skills_in_directory

        nonexistent = tmp_path / "does-not-exist"
        assert count_skills_in_directory(nonexistent) == 0
