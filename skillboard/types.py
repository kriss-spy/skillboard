"""Type aliases and type hints for skillboard."""

from pathlib import Path
from typing import TypeAlias

# Basic type aliases
SkillName: TypeAlias = str
SkillPath: TypeAlias = Path
SkillSet: TypeAlias = set[SkillName]

# Configuration types
AgentName: TypeAlias = str
PathAlias: TypeAlias = str
