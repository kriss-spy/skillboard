"""Type aliases and type hints for skillboard."""

from pathlib import Path

# Basic type aliases
SkillName = str
SkillPath = Path
SkillSet = set[SkillName]

# Configuration types
AgentName = str
PathAlias = str
