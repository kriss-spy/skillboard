# Skillboard

A lightweight skill management utility for AI coding agents. Toggle skills on/off between your warehouse and active directories using symbolic links.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/skillboard.svg)](https://pypi.org/project/skillboard/)

## Features

- ✨ **Simple Interactive UI** - Checkbox-based selection using `inquirer`
- 🔗 **Symbolic Links** - Efficiently enable/disable skills without copying
- 📂 **Multi-Agent Support** - Works with Claude Code, OpenCode, Gemini CLI, and more
- ⚡ **Fast Operations** - Quickly toggle skills with keyboard shortcuts
- 🎨 **Beautiful Output** - Rich terminal tables and colored output
- 🔧 **Configurable Paths** - Customize skill directories via config file
- 📋 **Copy & Move** - Copy or move skills between directories
- 👁️ **Read Skills** - View skill content without opening an editor
- 🧹 **Cleanup Orphaned Links** - Remove broken symlinks when skills are deleted
- 📦 **Install from GitHub** - Install skills directly from GitHub repos

## Installation

### Using pipx (Recommended)

```bash
pipx install skillboard
```

### Using pip

```bash
pip install skillboard
```

### From Source

```bash
git clone https://github.com/kriss-spy/skillboard.git
cd skillboard
pip install -e .
```

## Quick Start

### 1. Initialize directories

```bash
skillboard init
```

This creates the default skill directories:
- `~/.agents/skill-warehouse` - Your skill source of truth
- `~/.agents/skills` - Standard agent skills
- `~/.claude/skills` - Claude Code skills
- `~/.config/opencode/skills` - OpenCode skills
- `~/.gemini/skills` - Gemini CLI skills
- `~/.gemini/antigravity/skills` - Antigravity skills

### 2. List available skills

```bash
skillboard list              # Show all .agents skills (global + local)
skillboard list claude       # Show Claude skills (~/.claude/skills + ./.claude/skills)
skillboard list agent        # Show agent skills (~/.agents/skills + ./agents/skills)
skillboard list gemini       # Show Gemini skills (~/.gemini/skills + ./gemini/skills)
```

### 3. Link skills interactively

```bash
# Link from warehouse to Claude Code (interactive selection)
skillboard link -o claude

# Or specify source explicitly
skillboard link -i warehouse -o claude

# Using paths directly
skillboard link -i ~/.agents/skill-warehouse -o ~/.claude/skills

# Non-interactive mode (just list skills)
skillboard link -o claude --no-tui
```

### 4. Install skills from GitHub

```bash
# Install from Vercel Labs skills collection
skillboard install vercel-labs/skills -o warehouse --subpath skills

# Install a single skill repo
skillboard install owner/my-skill-repo -o warehouse
```

### 5. Copy or move skills

```bash
# Copy skills from warehouse to agent (interactive selection)
skillboard copy -i warehouse -o agent

# Copy all skills without selection
skillboard copy -i warehouse -o agent --all

# Move skills (copy + delete from source)
skillboard move -i warehouse -o agent

# Preview what would be moved
skillboard move -i warehouse -o agent --dry-run
```

### 6. Clean up orphaned symlinks

```bash
# Clean default agent skills
skillboard cleanup

# Clean specific agent skills
skillboard cleanup claude

# Preview what would be removed
skillboard cleanup --dry-run

# Remove without confirmation
skillboard cleanup --all
```

## Commands

### `init`

Initialize skillboard configuration and create default directories.

```bash
skillboard init

# Migrate old .agent paths to .agents (v0.2.0 to v0.3.0+)
skillboard init --migrate
```

### `list`

List available skills from both global and local locations.

```bash
skillboard list              # Show .agents skills (~/.agents/skills + ./.agents/skills)
skillboard list claude       # Show Claude skills (~/.claude/skills + ./.claude/skills)
skillboard list agent        # Show agent skills (~/.agents/skills + ./agents/skills)
skillboard list gemini       # Show Gemini skills (~/.gemini/skills + ./gemini/skills)
```

Shows skills from:
- **Global**: The agent's directory in home (e.g., `~/.claude/skills`)
- **Local**: The agent's directory in current project (e.g., `./.claude/skills`)

### `list-path`

Show all configured skill paths and their existence status.

```bash
skillboard list-path
```

### `link`

Create symbolic links to skills in the target directory. This is the primary command for enabling/disabling skills.

**Interactive mode (default):**
```bash
# Link from global skills (default)
skillboard link -o claude

# Link from warehouse to agent
skillboard link -i warehouse -o agent

# Link from local skills
skillboard link -i agent --input-scope local -o claude

# Link from local to local
skillboard link -i agent --input-scope local -o claude --output-scope local
```

**Non-interactive mode:**
```bash
skillboard link -o claude --no-tui
```

**Options:**
- `-i, --input`: Source agent or path
- `-o, --output`: Target agent or path (required)
- `--input-scope`: `global` or `local` for input
- `--output-scope`: `global` or `local` for output
- `--all`: Include both global and local sources
- `--no-tui`: Run in list-only mode
- `--verbose`: Show full table instead of summary

### `copy`

Copy skills from source to target (creates actual copies, not symlinks).

**Interactive mode (default):**
```bash
# Copy from warehouse to agent (interactive selection)
skillboard copy -i warehouse -o agent

# Copy from claude to agent
skillboard copy -i claude -o agent

# Copy from local source
skillboard copy -i agent --input-scope local -o warehouse
```

**Copy all without selection:**
```bash
skillboard copy -i warehouse -o agent --all
```

**Options:**
- `-i, --input`: Source agent or path (required)
- `-o, --output`: Target agent or path (required)
- `--input-scope`: `global` or `local` for input
- `--output-scope`: `global` or `local` for output
- `--all`: Copy all skills without interactive selection

### `move`

Move skills from source to target (copy + delete from source). **Use with caution** - this permanently deletes skills from the source location.

**Interactive mode (default):**
```bash
# Move from warehouse to agent (interactive selection)
skillboard move -i warehouse -o agent

# Move from claude to agent
skillboard move -i claude -o agent
```

**Move all without selection:**
```bash
skillboard move -i warehouse -o agent --all
```

**Preview before moving:**
```bash
skillboard move -i warehouse -o agent --dry-run
```

**Force overwrite existing skills:**
```bash
skillboard move -i warehouse -o agent --force
```

**Options:**
- `-i, --input`: Source agent or path (required)
- `-o, --output`: Target agent or path (required)
- `--input-scope`: `global` or `local` for input
- `--output-scope`: `global` or `local` for output
- `--all`: Move all skills without interactive selection
- `--dry-run`: Show what would be moved without actually moving
- `--force`: Overwrite existing skills in target without prompting

### `install`

Install skills from a GitHub repository. Automatically downloads and extracts skills to your warehouse.

**Install from GitHub (owner/repo format):**
```bash
# Install from Vercel Labs skills collection
skillboard install vercel-labs/skills -o warehouse --subpath skills

# Install a single skill repo
skillboard install owner/my-skill-repo -o warehouse

# Install from a specific branch
skillboard install vercel-labs/skills -o warehouse --subpath skills --branch main

# Install with force (overwrite existing)
skillboard install vercel-labs/skills -o warehouse --subpath skills --force
```

**Install from full GitHub URL:**
```bash
skillboard install https://github.com/vercel-labs/skills -o warehouse --subpath skills
```

**Auto-detection:**
The install command automatically detects:
- Single skill repos (contain SKILL.md in root)
- Multi-skill repos with `skills/` subdirectory
- Custom subpaths via `--subpath`

**Options:**
- `-o, --output`: Target agent or path (default: warehouse)
- `--branch`: Git branch to install from (default: main)
- `--subpath`: Subpath within repo where skills are located
- `--force`: Overwrite existing skills

### `cleanup`

Remove orphaned symlinks from target directories. Orphaned skills are symlinks that point to source directories which no longer exist (commonly after deleting a skill from the warehouse).

**Basic usage:**
```bash
skillboard cleanup                    # Clean default agent skills
skillboard cleanup claude             # Clean Claude skills
skillboard cleanup --scope local      # Clean local skills
```

**Preview before cleaning:**
```bash
skillboard cleanup --dry-run          # Show what would be removed
```

**Skip confirmation:**
```bash
skillboard cleanup --all              # Remove without prompting
```

**Options:**
- `agent`: Agent to clean (claude, agent, gemini, opencode, antigravity)
- `--scope`: `global` or `local`
- `--dry-run`: Preview without removing
- `--all`: Remove all without confirmation

### `read`

Display skill content for quick reference without opening an editor.

```bash
# Read skill from default agent location
skillboard read my-skill

# Read skill from specific agent
skillboard read my-skill -a claude

# Read from local scope
skillboard read my-skill -a agent --scope local

# Read from .github/skills
skillboard read my-skill --github
```

**Options:**
- `-a, --agent`: Agent to read from (claude, agent, gemini, opencode, antigravity)
- `--scope`: `global` or `local`
- `--github`: Read from `.github/skills` directory

## Available Aliases

The following aliases can be used with `-i` and `-o` options:

- `warehouse`: `~/.agents/skill-warehouse`
- `agent`: `~/.agents/skills`
- `claude`: `~/.claude/skills`
- `opencode`: `~/.config/opencode/skills`
- `gemini`: `~/.gemini/skills`
- `antigravity`: `~/.gemini/antigravity/skills`

## How It Works

Skillboard treats your **warehouse** (`~/.agents/skill-warehouse`) as the source of truth. When you "enable" a skill:

1. A symbolic link is created in the target directory pointing to the skill in the warehouse
2. The AI agent sees the skill and loads it

When you "disable" a skill:

1. The symbolic link is removed from the target directory
2. The AI agent no longer sees the skill

This approach:
- ✅ Keeps one master copy of each skill
- ✅ Instantly adds/removes skills from agent context
- ✅ Prevents context bloat by only having enabled skills visible
- ✅ Saves disk space (no copies needed)

## Configuration

Configuration is stored in `~/.config/skillboard/config.yaml`:

```yaml
paths:
  agent: ~/.agents/skills
  antigravity: ~/.gemini/antigravity/skills
  claude: ~/.claude/skills
  gemini: ~/.gemini/skills
  opencode: ~/.config/opencode/skills
  warehouse: ~/.agents/skill-warehouse
```

You can customize these paths by editing the config file.

## Development

```bash
# Clone the repository
git clone https://github.com/kriss-spy/skillboard.git
cd skillboard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black skillboard/
ruff check --fix skillboard/

# Type check
mypy skillboard/
```

## Project Structure

```
skillboard/
├── skillboard/
│   ├── __init__.py      # Package metadata
│   ├── cli.py           # CLI commands
│   ├── config.py        # Configuration management
│   ├── manager.py       # Skill scanning & symlink operations
│   └── tui.py           # Interactive checkbox interface
├── pyproject.toml       # Package configuration
├── LICENSE              # MIT License
└── README.md            # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [OpenSkills](https://github.com/numman-ali/openskills) for the checkbox interface pattern
- Built with [Click](https://click.palletsprojects.com/) for CLI and [Rich](https://rich.readthedocs.io/) for beautiful output
- Uses [inquirer](https://github.com/magmax/python-inquirer) for interactive prompts
