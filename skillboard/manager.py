"""Skill management operations."""

import os
from pathlib import Path
from typing import List, Set, Tuple
from dataclasses import dataclass


@dataclass
class Skill:
    """Represents a skill in the warehouse or target directory.

    Attributes:
        name: Name of the skill (directory name)
        path: Path to the skill directory
        is_enabled: Whether the skill is currently enabled (symlinked)
        is_symlink: Whether the skill is enabled as a symlink
    """

    name: str
    path: Path
    is_enabled: bool = False
    is_symlink: bool = False

    def __str__(self) -> str:
        status = "✓" if self.is_enabled else "✗"
        link_type = " (link)" if self.is_symlink else ""
        return f"{status} {self.name}{link_type}"


class SkillManager:
    """Manages skills in warehouse and target directories using symbolic links.

    This class provides operations to scan, enable, and disable skills by creating
    or removing symbolic links from the target directory to the source (warehouse).
    """

    def __init__(self, source_path: Path, target_path: Path):
        """Initialize skill manager.

        Args:
            source_path: Path to the warehouse (source of truth)
            target_path: Path to the target directory where symlinks are created
        """
        self.source_path = Path(source_path).resolve()
        self.target_path = Path(target_path).resolve()

        # Ensure directories exist
        self.source_path.mkdir(parents=True, exist_ok=True)
        self.target_path.mkdir(parents=True, exist_ok=True)

    def scan_skills(self) -> List[Skill]:
        """Scan both source and target directories to get all skills.

        Returns:
            List of Skill objects with their status, sorted alphabetically
        """
        skills: List[Skill] = []

        # Get all skills from source (warehouse)
        if self.source_path.exists():
            for item in sorted(self.source_path.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    skills.append(
                        Skill(name=item.name, path=item, is_enabled=False, is_symlink=False)
                    )

        # Check which skills are enabled in target
        if self.target_path.exists():
            for item in self.target_path.iterdir():
                if item.name.startswith("."):
                    continue

                target_full_path = self.target_path / item.name

                # Check if it's a symlink pointing to source
                if target_full_path.is_symlink():
                    resolved = target_full_path.resolve()
                    source_candidate = (self.source_path / item.name).resolve()

                    if resolved == source_candidate:
                        # Find and update the skill
                        for skill in skills:
                            if skill.name == item.name:
                                skill.is_enabled = True
                                skill.is_symlink = True
                                break
                        else:
                            # Skill exists in target but not source (orphaned)
                            skills.append(
                                Skill(
                                    name=item.name,
                                    path=target_full_path,
                                    is_enabled=True,
                                    is_symlink=True,
                                )
                            )
                elif target_full_path.is_dir():
                    # Regular directory (not a symlink)
                    for skill in skills:
                        if skill.name == item.name:
                            skill.is_enabled = True
                            skill.is_symlink = False
                            break

        return sorted(skills, key=lambda s: s.name.lower())

    def enable_skill(self, skill_name: str) -> bool:
        """Enable a skill by creating a symlink from source to target.

        Args:
            skill_name: Name of the skill to enable

        Returns:
            True if successful, False otherwise
        """
        source_skill = self.source_path / skill_name
        target_skill = self.target_path / skill_name

        # Check if source exists
        if not source_skill.exists():
            print(f"Error: Skill '{skill_name}' not found in warehouse")
            return False

        # Check if already enabled
        if target_skill.exists():
            if target_skill.is_symlink():
                return True  # Already enabled, not an error
            else:
                print(f"Error: '{skill_name}' exists in target but is not a symlink")
                return False

        try:
            # Create relative symlink
            relative_source = os.path.relpath(source_skill, self.target_path)
            target_skill.symlink_to(relative_source, target_is_directory=True)
            return True
        except Exception as e:
            print(f"Error enabling skill '{skill_name}': {e}")
            return False

    def disable_skill(self, skill_name: str) -> bool:
        """Disable a skill by removing the symlink from target.

        Args:
            skill_name: Name of the skill to disable

        Returns:
            True if successful, False otherwise
        """
        target_skill = self.target_path / skill_name

        # Check if target exists
        if not target_skill.exists():
            return True  # Already disabled, not an error

        # Only remove if it's a symlink
        if not target_skill.is_symlink():
            print(f"Error: '{skill_name}' is not a symlink, won't remove")
            return False

        try:
            target_skill.unlink()
            return True
        except Exception as e:
            print(f"Error disabling skill '{skill_name}': {e}")
            return False

    def apply_changes(self, enabled_skills: Set[str]) -> Tuple[List[str], List[str]]:
        """Apply changes to match the desired set of enabled skills.

        Args:
            enabled_skills: Set of skill names that should be enabled

        Returns:
            Tuple of (enabled_list, disabled_list) showing what was changed
        """
        current_skills = self.scan_skills()
        currently_enabled = {s.name for s in current_skills if s.is_enabled}

        enabled: List[str] = []
        disabled: List[str] = []

        # Enable skills that should be enabled but aren't
        for skill_name in enabled_skills:
            if skill_name not in currently_enabled:
                if self.enable_skill(skill_name):
                    enabled.append(skill_name)

        # Disable skills that are enabled but shouldn't be
        for skill_name in currently_enabled:
            if skill_name not in enabled_skills:
                if self.disable_skill(skill_name):
                    disabled.append(skill_name)

        return enabled, disabled

    def get_source_skills(self) -> List[Skill]:
        """Get all skills available in the source (warehouse).

        Returns:
            List of skills from source directory
        """
        skills: List[Skill] = []
        if self.source_path.exists():
            for item in sorted(self.source_path.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    skills.append(
                        Skill(name=item.name, path=item, is_enabled=False, is_symlink=False)
                    )
        return skills

    def get_target_skills(self) -> List[Skill]:
        """Get all skills currently enabled in the target.

        Returns:
            List of skills from target directory
        """
        skills: List[Skill] = []
        if self.target_path.exists():
            for item in self.target_path.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_dir() or item.is_symlink():
                    skills.append(
                        Skill(
                            name=item.name,
                            path=item,
                            is_enabled=True,
                            is_symlink=item.is_symlink(),
                        )
                    )
        return skills
