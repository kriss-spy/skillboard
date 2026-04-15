"""Tests for move skill functionality."""

from skillboard.manager import SkillManager


class TestMoveSkill:
    """Tests for SkillManager.move_skill method."""

    def test_move_success(self, tmp_path):
        """Test successful move operation."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        # Create a skill
        skill = source / "test-skill"
        skill.mkdir()
        (skill / "file.txt").write_text("content")

        manager = SkillManager(source, target)
        success, message = manager.move_skill("test-skill")

        assert success is True
        assert message == "moved"
        assert not (source / "test-skill").exists()
        assert (target / "test-skill").exists()
        assert (target / "test-skill" / "file.txt").read_text() == "content"

    def test_move_missing_source(self, tmp_path):
        """Test moving a skill that doesn't exist."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        manager = SkillManager(source, target)
        success, message = manager.move_skill("missing-skill")

        assert success is False
        assert "not found" in message.lower()

    def test_move_conflict_without_force(self, tmp_path):
        """Test moving when target exists without force flag."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        # Create skill in both locations with different content
        source_skill = source / "test-skill"
        source_skill.mkdir()
        (source_skill / "file.txt").write_text("source content")

        target_skill = target / "test-skill"
        target_skill.mkdir()
        (target_skill / "file.txt").write_text("target content")

        manager = SkillManager(source, target)
        success, message = manager.move_skill("test-skill", force=False)

        assert success is False
        assert message == "conflict"

    def test_move_identical_skips(self, tmp_path):
        """Test moving identical skills skips without error."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        # Create identical skills
        source_skill = source / "test-skill"
        source_skill.mkdir()
        (source_skill / "file.txt").write_text("same content")

        target_skill = target / "test-skill"
        target_skill.mkdir()
        (target_skill / "file.txt").write_text("same content")

        manager = SkillManager(source, target)
        success, message = manager.move_skill("test-skill")

        assert success is True
        assert message == "identical"
        # Source should still exist (not deleted since they're identical)
        assert (source / "test-skill").exists()

    def test_move_with_force(self, tmp_path):
        """Test moving with force flag overwrites target."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        # Create skill in both locations
        source_skill = source / "test-skill"
        source_skill.mkdir()
        (source_skill / "file.txt").write_text("new content")

        target_skill = target / "test-skill"
        target_skill.mkdir()
        (target_skill / "file.txt").write_text("old content")

        manager = SkillManager(source, target)
        success, message = manager.move_skill("test-skill", force=True)

        assert success is True
        assert message == "moved"
        assert not (source / "test-skill").exists()
        assert (target / "test-skill").exists()
        assert (target / "test-skill" / "file.txt").read_text() == "new content"

    def test_move_symlink_source(self, tmp_path):
        """Test moving a skill that is a symlink."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        # Create real skill somewhere else
        real_skill = tmp_path / "real-skill"
        real_skill.mkdir()
        (real_skill / "file.txt").write_text("content")

        # Create symlink in source
        source_skill = source / "test-skill"
        source_skill.symlink_to(real_skill)

        manager = SkillManager(source, target)
        success, message = manager.move_skill("test-skill")

        assert success is True
        assert message == "moved"
        assert not source_skill.exists()
        assert (target / "test-skill").exists()

    def test_move_symlink_identical_unlinks(self, tmp_path):
        """Test moving a symlink when target has identical content removes the symlink."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        # Create skill in target
        target_skill = target / "test-skill"
        target_skill.mkdir()
        (target_skill / "file.txt").write_text("same content")

        # Create symlink in source pointing to target
        source_skill = source / "test-skill"
        source_skill.symlink_to(target_skill)

        manager = SkillManager(source, target)
        success, message = manager.move_skill("test-skill")

        # Should succeed and remove the symlink
        assert success is True
        assert message == "unlinked"
        # Symlink should be removed from source
        assert not source_skill.exists()
        # Target should still exist
        assert (target / "test-skill").exists()
