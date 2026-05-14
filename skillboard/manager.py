"""Skill management operations."""

import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from rich.console import Console

console: Console = Console()


def get_skill_description(skill_path: Path, max_length: int = 80) -> str:
    """Extract description from a skill's SKILL.md frontmatter.

    Reads the YAML frontmatter (delimited by ---) and returns the
    value of the 'description' field, truncated to max_length.

    Args:
        skill_path: Path to the skill directory
        max_length: Maximum length of the returned description

    Returns:
        Description string, or empty string if not found
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return ""

    try:
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return ""

        # Find end of frontmatter
        end = content.find("\n---", 3)
        if end == -1:
            return ""

        frontmatter = content[3:end]
        data = yaml.safe_load(frontmatter) or {}
        desc = data.get("description", "")

        # Handle multiline/folded YAML strings
        if isinstance(desc, str):
            desc = " ".join(desc.split())
            if len(desc) > max_length:
                desc = desc[: max_length - 3].rstrip() + "..."
            return desc
    except Exception:
        pass

    return ""


def get_skill_content_hash(skill_path: Path) -> str:
    """Calculate SHA256 hash of skill directory contents.

    Hashes all files recursively, sorted by path to ensure consistent ordering.

    Args:
        skill_path: Path to the skill directory

    Returns:
        Hex digest of the content hash
    """
    sha256 = hashlib.sha256()

    if not skill_path.exists():
        return ""

    # Get all files sorted by path for consistency
    files = sorted(skill_path.rglob("*"))

    for file_path in files:
        if file_path.is_file():
            # Add relative path to hash
            rel_path = file_path.relative_to(skill_path).as_posix()
            sha256.update(rel_path.encode())
            sha256.update(b"\0")  # Separator

            # Add file content to hash
            try:
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        sha256.update(chunk)
            except OSError:
                # Skip files that can't be read
                sha256.update(b"<unreadable>")
            sha256.update(b"\0")  # Separator

    return sha256.hexdigest()[:16]  # Use first 16 chars for readability


def are_skills_identical(skill1_path: Path, skill2_path: Path) -> bool:
    """Check if two skill directories have identical content.

    Args:
        skill1_path: Path to first skill
        skill2_path: Path to second skill

    Returns:
        True if skills have identical content
    """
    return get_skill_content_hash(skill1_path) == get_skill_content_hash(skill2_path)


def count_skills_in_directory(path: Path) -> int:
    """Count non-hidden skill directories in a path.

    Args:
        path: Path to directory

    Returns:
        Number of skill directories (non-hidden, non-special)
    """
    if not path.exists():
        return 0

    count = 0
    for item in path.iterdir():
        if item.is_dir() and not item.name.startswith(".") and not item.name.startswith("__"):
            count += 1
    return count


@dataclass
class Skill:
    """Represents a skill in the warehouse or target directory.

    Attributes:
        name: Name of the skill (directory name)
        path: Path to the skill directory
        is_enabled: Whether the skill is currently enabled (symlinked)
        is_symlink: Whether the skill is enabled as a symlink
        description: Short description from SKILL.md frontmatter
    """

    name: str
    path: Path
    is_enabled: bool = False
    is_symlink: bool = False
    description: str = ""

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

    def scan_skills(self) -> list["Skill"]:
        """Scan both source and target directories to get all skills.

        Returns:
            List of Skill objects with their status, sorted alphabetically
        """
        skills: list[Skill] = []

        # Get all skills from source (warehouse)
        if self.source_path.exists():
            for item in sorted(self.source_path.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    desc = get_skill_description(item)
                    skills.append(
                        Skill(
                            name=item.name,
                            path=item,
                            is_enabled=False,
                            is_symlink=False,
                            description=desc,
                        )
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
                                    description="",
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
            console.print(f"[red]Error: Skill '{skill_name}' not found in warehouse[/red]")
            return False

        # Check if already enabled
        if target_skill.exists():
            if target_skill.is_symlink():
                return True  # Already enabled, not an error
            else:
                console.print(f"[red]Error: '{skill_name}' exists in target but is not a symlink[/red]")
                return False

        try:
            # Create absolute symlink (per agent skill standard)
            absolute_source = source_skill.resolve()
            target_skill.symlink_to(absolute_source, target_is_directory=True)
            return True
        except Exception as e:
            console.print(f"[red]Error enabling skill '{skill_name}': {e}[/red]")
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
            console.print(f"[yellow]Warning: '{skill_name}' is not a symlink, won't remove[/yellow]")
            return False

        try:
            target_skill.unlink()
            return True
        except Exception as e:
            console.print(f"[red]Error disabling skill '{skill_name}': {e}[/red]")
            return False

    def apply_changes(self, enabled_skills: set[str]) -> tuple[list[str], list[str]]:
        """Apply changes to match the desired set of enabled skills.

        Args:
            enabled_skills: Set of skill names that should be enabled

        Returns:
            Tuple of (enabled_list, disabled_list) showing what was changed
        """
        current_skills = self.scan_skills()
        currently_enabled = {s.name for s in current_skills if s.is_enabled}

        enabled: list[str] = []
        disabled: list[str] = []

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

    def get_source_skills(self) -> list["Skill"]:
        """Get all skills available in the source (warehouse).

        Returns:
            List of skills from source directory
        """
        skills: list[Skill] = []
        if self.source_path.exists():
            for item in sorted(self.source_path.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    desc = get_skill_description(item)
                    skills.append(
                        Skill(
                            name=item.name,
                            path=item,
                            is_enabled=False,
                            is_symlink=False,
                            description=desc,
                        )
                    )
        return skills

    def get_target_skills(self) -> list["Skill"]:
        """Get all skills currently enabled in the target.

        Returns:
            List of skills from target directory
        """
        skills: list[Skill] = []
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

    def find_orphaned_skills(self) -> list[Skill]:
        """Find orphaned symlinks in the target directory.

        An orphaned skill is a symlink in the target that points to a
        non-existent path (the source skill has been removed).

        Returns:
            List of orphaned Skill objects
        """
        orphaned: list[Skill] = []
        if not self.target_path.exists():
            return orphaned

        for item in self.target_path.iterdir():
            if item.name.startswith("."):
                continue

            if item.is_symlink():
                try:
                    resolved = item.resolve()
                    if not resolved.exists():
                        orphaned.append(
                            Skill(
                                name=item.name,
                                path=item,
                                is_enabled=True,
                                is_symlink=True,
                                description="",
                            )
                        )
                except (OSError, RuntimeError):
                    # Broken symlink or permission error
                    orphaned.append(
                        Skill(
                            name=item.name,
                            path=item,
                            is_enabled=True,
                            is_symlink=True,
                            description="",
                        )
                    )

        return sorted(orphaned, key=lambda s: s.name.lower())

    def remove_orphaned_skill(self, skill_name: str) -> bool:
        """Remove an orphaned symlink from the target directory.

        Args:
            skill_name: Name of the orphaned skill to remove

        Returns:
            True if successfully removed, False otherwise
        """
        target_skill = self.target_path / skill_name

        if not target_skill.exists():
            return True  # Already gone

        if not target_skill.is_symlink():
            console.print(f"[yellow]Warning: '{skill_name}' is not a symlink, skipping[/yellow]")
            return False

        try:
            target_skill.unlink()
            return True
        except Exception as e:
            console.print(f"[red]Error removing orphaned skill '{skill_name}': {e}[/red]")
            return False

    def move_skill(self, skill_name: str, force: bool = False) -> tuple[bool, str]:
        """Move a skill from source to target with rollback support.

        This is an atomic operation that either succeeds completely or
        rolls back any partial changes.

        Args:
            skill_name: Name of the skill to move
            force: Whether to overwrite existing skills in target

        Returns:
            Tuple of (success, message)
        """
        source_skill = self.source_path / skill_name
        target_skill = self.target_path / skill_name

        # Validate source exists
        if not source_skill.exists():
            return False, f"Skill '{skill_name}' not found in source"

        # Check target conflicts
        if target_skill.exists():
            if not force:
                if are_skills_identical(source_skill, target_skill):
                    # Skills are identical - if source is a symlink, just remove it
                    # since it points to the same content already in target
                    if source_skill.is_symlink():
                        try:
                            source_skill.unlink()
                            return True, "unlinked"
                        except Exception as e:
                            return False, f"Error removing symlink: {e}"
                    return True, "identical"
                return False, "conflict"

            # Force: remove existing target
            try:
                if target_skill.is_symlink():
                    target_skill.unlink()
                else:
                    shutil.rmtree(target_skill)
            except Exception as e:
                return False, f"Error removing existing: {e}"

        # Step 1: Copy to target
        try:
            shutil.copytree(source_skill, target_skill)
        except Exception as e:
            return False, f"Error copying: {e}"

        # Step 2: Remove from source (with rollback on failure)
        try:
            if source_skill.is_symlink():
                source_skill.unlink()
            else:
                shutil.rmtree(source_skill)
        except Exception as e:
            # Rollback: remove copied skill from target
            try:
                if target_skill.is_symlink():
                    target_skill.unlink()
                else:
                    shutil.rmtree(target_skill)
            except Exception:
                pass  # Best effort rollback
            return False, f"Error deleting from source (rolled back): {e}"

        return True, "moved"
