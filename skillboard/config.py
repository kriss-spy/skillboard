"""Configuration management for skillboard."""

from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field

import yaml


@dataclass
class SkillPaths:
    """Configuration for skill directories.

    Attributes:
        warehouse: Source of truth for all skills
        agent: Standard agent skills directory
        claude: Claude Code skills directory
        opencode: OpenCode skills directory
        gemini: Gemini CLI skills directory
        antigravity: Antigravity skills directory
    """

    warehouse: Path = field(default_factory=lambda: Path.home() / ".agent" / "skill-warehouse")
    agent: Path = field(default_factory=lambda: Path.home() / ".agent" / "skills")
    claude: Path = field(default_factory=lambda: Path.home() / ".claude" / "skills")
    opencode: Path = field(default_factory=lambda: Path.home() / ".config" / "opencode" / "skills")
    gemini: Path = field(default_factory=lambda: Path.home() / ".gemini" / "skills")
    antigravity: Path = field(
        default_factory=lambda: Path.home() / ".gemini" / "antigravity" / "skills"
    )

    def get_path(self, name: str) -> Path:
        """Get skill path by name.

        Args:
            name: Alias name of the path

        Returns:
            Path object for the alias

        Raises:
            ValueError: If the alias is not recognized
        """
        paths = self.list_paths()
        if name not in paths:
            raise ValueError(f"Unknown skill path: {name}. Available: {', '.join(paths.keys())}")
        return paths[name]

    def list_paths(self) -> Dict[str, Path]:
        """List all available skill paths.

        Returns:
            Dictionary mapping alias names to paths
        """
        return {
            "warehouse": self.warehouse,
            "agent": self.agent,
            "claude": self.claude,
            "opencode": self.opencode,
            "gemini": self.gemini,
            "antigravity": self.antigravity,
        }


class Config:
    """Configuration manager for skillboard.

    Handles loading and saving configuration from/to YAML files.
    """

    CONFIG_FILE: Path = Path.home() / ".config" / "skillboard" / "config.yaml"

    def __init__(self):
        """Initialize configuration with defaults and load from file."""
        self.paths = SkillPaths()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if not self.CONFIG_FILE.exists():
            return

        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Override default paths with config values
            if "paths" in data:
                for key, value in data["paths"].items():
                    if hasattr(self.paths, key):
                        setattr(self.paths, key, Path(value))
        except Exception as e:
            print(f"Warning: Failed to load config from {self.CONFIG_FILE}: {e}")

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

            data = {"paths": {key: str(path) for key, path in self.paths.list_paths().items()}}

            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=True)
        except Exception as e:
            print(f"Warning: Failed to save config to {self.CONFIG_FILE}: {e}")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config instance (creates one if it doesn't exist)
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance.

    Useful for testing.
    """
    global _config
    _config = None
