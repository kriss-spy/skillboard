# Skillboard

A lightweight skill management utility for AI coding agents. Toggle skills on/off between your warehouse and active directories using symbolic links.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/skillboard.svg)](https://badge.fury.io/py/skillboard)

## Features

- ✨ **Simple Interactive UI** - Checkbox-based selection using `inquirer`
- 🔗 **Symbolic Links** - Efficiently enable/disable skills without copying
- 📂 **Multi-Agent Support** - Works with Claude Code, OpenCode, Gemini CLI, and more
- ⚡ **Fast Operations** - Quickly toggle skills with keyboard shortcuts
- 🎨 **Beautiful Output** - Rich terminal tables and colored output
- 🔧 **Configurable Paths** - Customize skill directories via config file

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
- `~/.agent/skill-warehouse` - Your skill source of truth
- `~/.agent/skills` - Standard agent skills
- `~/.claude/skills` - Claude Code skills
- `~/.config/opencode/skills` - OpenCode skills
- `~/.gemini/skills` - Gemini CLI skills
- `~/.gemini/antigravity/skills` - Antigravity skills

### 2. List available skills

```bash
skillboard list  # Show all skills in warehouse
```

### 3. List configured paths

```bash
skillboard list-path
```

### 3. Sync skills interactively

```bash
# Sync from warehouse to Claude Code
skillboard sync -o claude

# Or specify source explicitly
skillboard sync -i warehouse -o claude

# Using paths directly
skillboard sync -i ~/.agent/skill-warehouse -o ~/.claude/skills
```

### 4. List skills without interactive mode

```bash
skillboard sync -o claude --no-tui
```

## Commands

### `init`
Initialize skillboard configuration and create default directories.

```bash
skillboard init
```

### `list`
List available skills in the warehouse.

```bash
skillboard list  # Show all warehouse skills
```

Shows skills from the warehouse directory (`~/.agent/skill-warehouse`).

### `list-path`
Show all configured skill paths and their existence status.

```bash
skillboard list-path
```

### `sync`
Sync skills between warehouse and target directory.

**Interactive mode (default):**
```bash
skillboard sync -o claude
```

Shows a checkbox interface:
- **Space**: Toggle skill on/off
- **Enter**: Confirm selection
- Shows preview of changes before applying

**List-only mode:**
```bash
skillboard sync -o claude --no-tui
```

**Options:**
- `-i, --input`: Source directory (default: warehouse)
- `-o, --output`: Target directory (required)
- `--no-tui`: Run in list-only mode

**Available aliases:**
- `warehouse`: `~/.agent/skill-warehouse`
- `agent`: `~/.agent/skills`
- `claude`: `~/.claude/skills`
- `opencode`: `~/.config/opencode/skills`
- `gemini`: `~/.gemini/skills`
- `antigravity`: `~/.gemini/antigravity/skills`

### `copy`
Copy skills from source to target (creates actual copies, not symlinks).

```bash
skillboard copy warehouse claude
```

## How It Works

Skillboard treats your **warehouse** (`~/.agent/skill-warehouse`) as the source of truth. When you "enable" a skill:

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
  agent: ~/.agent/skills
  antigravity: ~/.gemini/antigravity/skills
  claude: ~/.claude/skills
  gemini: ~/.gemini/skills
  opencode: ~/.config/opencode/skills
  warehouse: ~/.agent/skill-warehouse
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
