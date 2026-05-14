# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-05-14

### Added
- Skill descriptions auto-extracted from SKILL.md YAML frontmatter
  - `link --verbose` now shows a Description column in the skills table
  - Interactive TUI (link/copy/move) displays a Name + Description table before selection
  - Descriptions are read from the `description` field in YAML frontmatter
  - Long descriptions are truncated to 80 characters with ellipsis
  - Supports quoted, unquoted, and multiline folded YAML strings
- 7 new tests for description extraction covering all edge cases

## [1.2.0] - 2026-05-12

### Added
- New `cleanup` command to remove orphaned symlinks
  - Detects broken symlinks pointing to deleted source skills
  - Supports `--dry-run` to preview what would be removed
  - Supports `--all` to skip confirmation prompt
  - Works with any agent and both global/local scopes
- Python 3.14 support
  - Added classifier to `pyproject.toml`
  - All 82 tests pass on Python 3.14.4

### Fixed
- Eliminated all bare `print()` statements across the codebase
  - `manager.py`: error/warning messages now use `console.print()` with Rich styling
  - `config.py`: config load/save warnings now use `console.print()` with Rich styling
  - Consistent with the error handling module introduced in v1.0.0

### Changed
- Expanded test suite from 55 to 82 tests (+27 tests)
  - Added comprehensive tests for `cleanup` command (14 tests)
  - Added tests for `read` command (8 tests)
  - Added tests for `copy` command (4 tests)
  - Better CLI test coverage with proper config mocking

## [1.1.0] - 2026-04-15

### Added
- New `install` command to fetch skills from GitHub repositories
  - Supports `owner/repo` format: `skillboard install vercel-labs/skills --subpath skills`
  - Supports full GitHub URLs: `skillboard install https://github.com/vercel-labs/skills --subpath skills`
  - Custom subpath support for repos like `vercel-labs/skills`
  - Auto-detects single skill vs multi-skill repositories
  - Downloads and extracts with progress indicators
  - Force flag to overwrite existing skills
  - Defaults to installing to warehouse

## [1.0.1] - 2026-04-15

### Fixed
- Move command now properly handles linked skills
  - When moving a symlink pointing to identical content, removes the symlink
  - Previously would skip and leave symlink in place (confusing behavior)
  - Now shows "✓ Unlinked" message
  - Added test: `test_move_symlink_identical_unlinks`

## [1.0.0] - 2026-04-15

### Added
- Atomic move operations with automatic rollback
  - If copy succeeds but delete fails, copied skill is removed from target
  - Prevents partial move states
- Comprehensive test suite (54 tests, up from 24)
  - Path resolution tests
  - Error handling tests
  - Move skill tests with rollback scenarios
- Type safety improvements
  - Type aliases in `skillboard/types.py`
  - Typed console variables across modules
- Error handling module with standardized exit codes
  - `ExitCode` enum with specific codes for different errors
  - `error()`, `warning()`, `info()`, `success()`, `cancel()` functions
- Path resolution module
  - Extracted from CLI to reduce code duplication
  - `resolve_source_path()`, `resolve_target_path()` functions
  - `validate_source_exists()`, `ensure_target_directory()` helpers

### Changed
- Dynamic version resolution from package metadata
  - Single source of truth in `pyproject.toml`
  - Uses `importlib.metadata` for version detection
- Documentation completely rewritten
  - Removed non-existent `sync` command references
  - Added complete documentation for all 7 commands
  - Fixed all command examples with correct syntax
  - Added documentation for `--all`, `--dry-run`, `--force` flags

### Fixed
- TUI pre-selection bug in copy/move commands
  - No longer pre-selects all skills when user doesn't choose
- Exception handling clarity
  - `ImportError` now shows helpful installation message
  - `KeyboardInterrupt` shows simple cancellation message
- Move command now handles partial failures gracefully
- All paths in README now use correct `.agents` plural form

### Removed
- Unused `pydantic` dependency
- Hardcoded version in `__init__.py` (now dynamic)
- Duplicate path resolution logic across CLI commands

## [0.3.2] - 2026-04-15

### Added
- Interactive TUI for copy and move commands
- `[Select All]` option in skill selection
- `--all` flag for copy/move commands

## [0.3.1] - 2026-04-15

### Fixed
- Migration support for `.agent` to `.agents` path change

## [0.3.0] - 2026-04-15

### Changed
- **Breaking**: Changed default paths from `.agent` to `.agents`
- Added `init --migrate` flag for migrating old paths

## [0.2.0] - 2026-04-14

### Added
- Initial release with core functionality
- `link`, `list`, `list-path`, `init`, `copy`, `move`, `read` commands
- Symbolic link management
- Interactive TUI with checkbox selection
- Multi-agent support (Claude, OpenCode, Gemini, etc.)
