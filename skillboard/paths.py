"""Path resolution utilities for skillboard.

Provides consistent path resolution across all CLI commands.
"""

from pathlib import Path
from typing import Optional

from .errors import ExitCode, error


def resolve_agent_path(
    agent_name: str,
    scope: str,
    config,
) -> Path:
    """Resolve an agent name to an actual path.

    Args:
        agent_name: Name of the agent (claude, agent, gemini, etc.)
        scope: 'global' or 'local'
        config: Config instance with path mappings

    Returns:
        Resolved Path object

    Raises:
        SystemExit: If agent name is unknown
    """
    agent_lower = agent_name.lower()

    if agent_lower in config.paths.list_paths():
        if scope == "local":
            return Path(f"./.{agent_lower}/skills")
        else:
            return config.paths.get_path(agent_lower)
    else:
        available = ", ".join(config.paths.list_paths().keys())
        error(f"Unknown agent '{agent_name}'. Available: {available}", ExitCode.INVALID_ARGUMENTS)


def resolve_source_path(
    input_path: Optional[str],
    scope: str,
    config,
) -> Path:
    """Resolve source path from input string.

    Args:
        input_path: Agent name, alias, or explicit path
        scope: 'global' or 'local'
        config: Config instance with path mappings

    Returns:
        Resolved Path object

    Raises:
        SystemExit: If input_path is invalid
    """
    if input_path is None:
        error("Source is required. Use -i/--input option.", ExitCode.INVALID_ARGUMENTS)

    # Check if it's an agent alias
    agent_lower = input_path.lower()
    if agent_lower in config.paths.list_paths():
        return resolve_agent_path(agent_lower, scope, config)

    # Treat as explicit path
    return Path(input_path).expanduser()


def resolve_target_path(
    output_path: Optional[str],
    scope: str,
    config,
) -> Path:
    """Resolve target path from output string.

    Args:
        output_path: Agent name, alias, or explicit path
        scope: 'global' or 'local'
        config: Config instance with path mappings

    Returns:
        Resolved Path object

    Raises:
        SystemExit: If output_path is invalid
    """
    if output_path is None:
        error("Target is required. Use -o/--output option.", ExitCode.INVALID_ARGUMENTS)

    # Check if it's an agent alias
    agent_lower = output_path.lower()
    if agent_lower in config.paths.list_paths():
        return resolve_agent_path(agent_lower, scope, config)

    # Treat as explicit path
    return Path(output_path).expanduser()


def resolve_link_source(
    input_path: Optional[str],
    input_scope: str,
    link_all: bool,
    config,
) -> Path:
    """Resolve source path specifically for the link command.

    The link command has special handling for --all flag.

    Args:
        input_path: Agent name or None (defaults to 'agent')
        input_scope: 'global' or 'local'
        link_all: Whether --all flag is set
        config: Config instance

    Returns:
        Resolved source Path
    """
    # Determine source agent
    if input_path is None:
        source_agent = "agent"
    else:
        source_agent = input_path.lower()

    if link_all:
        # For --all, we use global path by default
        if source_agent in config.paths.list_paths():
            return config.paths.get_path(source_agent)
        else:
            error(f"Unknown source agent: {source_agent}", ExitCode.INVALID_ARGUMENTS)

    # Single source
    return resolve_source_path(input_path or source_agent, input_scope, config)


def validate_source_exists(path: Path) -> None:
    """Validate that source path exists.

    Args:
        path: Path to validate

    Raises:
        SystemExit: If path doesn't exist
    """
    if not path.exists():
        error(f"Source does not exist: {path}", ExitCode.SOURCE_NOT_FOUND)


def ensure_target_directory(path: Path) -> None:
    """Ensure target directory exists (create if needed).

    Args:
        path: Target path to ensure
    """
    path.mkdir(parents=True, exist_ok=True)
