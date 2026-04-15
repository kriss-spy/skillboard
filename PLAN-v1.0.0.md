# Skillboard v1.0.0 Production Release Plan

## Overview

This document outlines the roadmap for Skillboard v1.0.0 - the first production-ready release. It addresses all identified technical debt, documentation flaws, bugs, and quality issues discovered in the v0.3.x codebase.

**Target Release Date:** TBD (estimated 4-6 weeks of development)
**Current Version:** v0.3.2
**Status:** In Planning

---

## Goals for v1.0.0

1. **Stability**: All critical bugs fixed, edge cases handled
2. **Consistency**: Unified API, consistent error handling, no version mismatches
3. **Completeness**: All documented features actually exist and work
4. **Quality**: Full type safety, comprehensive tests (>90% coverage)
5. **Documentation**: Accurate, complete, with examples

---

## Phase 1: Critical Fixes (Week 1)

### 1.1 Version Synchronization
**Priority:** 🔴 CRITICAL

**Problem:** `__init__.py` version (0.3.1) doesn't match `pyproject.toml` (0.3.2)

**Solution:**
- Create single source of truth for version
- Use `importlib.metadata` to read version from package metadata
- Update both files to use dynamic version resolution

**Acceptance Criteria:**
- [ ] `skillboard --version` returns correct version
- [ ] Version defined in exactly one place
- [ ] CI verifies version consistency

**Files to Modify:**
- `skillboard/__init__.py`
- `pyproject.toml`

---

### 1.2 Remove Non-Existent Command Documentation
**Priority:** 🔴 CRITICAL

**Problem:** README extensively documents `sync` command that doesn't exist

**Solution:**
- Remove all `sync` command references from README
- Update quick start examples to use actual `link` command
- Document `link` command properly

**Acceptance Criteria:**
- [ ] No references to non-existent commands in README
- [ ] All documented commands exist in CLI
- [ ] Examples use correct syntax

**Files to Modify:**
- `README.md`

---

### 1.3 Fix Command Examples
**Priority:** 🔴 CRITICAL

**Problem:** `copy` command example uses wrong syntax

**Current (WRONG):**
```bash
skillboard copy warehouse claude
```

**Correct:**
```bash
skillboard copy -i warehouse -o claude
```

**Acceptance Criteria:**
- [ ] All command examples tested and verified
- [ ] Examples match actual CLI interface
- [ ] Include `--all` flag examples

**Files to Modify:**
- `README.md`

---

## Phase 2: Architecture Improvements (Week 2)

### 2.1 Extract Path Resolution Logic
**Priority:** 🟡 HIGH

**Problem:** Path resolution code duplicated in 4 commands (`link`, `copy`, `move`, `read`)

**Solution:**
```python
# New module: skillboard/paths.py

def resolve_source_path(
    input_path: Optional[str],
    scope: str,
    config: Config
) -> Path:
    """Resolve source path from agent name or explicit path."""
    ...

def resolve_target_path(
    output_path: Optional[str],
    scope: str,
    config: Config
) -> Path:
    """Resolve target path from agent name or explicit path."""
    ...
```

**Acceptance Criteria:**
- [ ] Path resolution logic extracted to shared module
- [ ] All commands use shared functions
- [ ] Unit tests for path resolution (>95% coverage)
- [ ] No code duplication

**Files to Create/Modify:**
- `skillboard/paths.py` (new)
- `skillboard/cli.py`
- `tests/test_paths.py` (new)

---

### 2.2 Consolidate Error Handling
**Priority:** 🟡 HIGH

**Problem:** Inconsistent error handling - some use `print()`, some use `console`, some use `click.echo()`

**Solution:**
- Create unified error handling module
- All errors go through `console.print()` with consistent formatting
- Define error codes/exit codes

**Pattern:**
```python
# skillboard/errors.py
from enum import IntEnum

class ExitCode(IntEnum):
    SUCCESS = 0
    INVALID_ARGUMENTS = 1
    SOURCE_NOT_FOUND = 2
    TARGET_NOT_FOUND = 3
    PERMISSION_DENIED = 4
    OPERATION_FAILED = 5

def error(message: str, code: ExitCode = ExitCode.OPERATION_FAILED) -> None:
    console.print(f"[red]Error: {message}[/red]")
    sys.exit(code)
```

**Acceptance Criteria:**
- [ ] All errors use consistent formatting
- [ ] Appropriate exit codes for different error types
- [ ] All error messages user-friendly
- [ ] No bare `print()` statements in codebase

**Files to Create/Modify:**
- `skillboard/errors.py` (new)
- `skillboard/cli.py`
- `skillboard/manager.py`

---

### 2.3 Remove Unused Dependencies
**Priority:** 🟡 HIGH

**Problem:** `pydantic` is listed as dependency but never used

**Solution:**
- Remove `pydantic` from `pyproject.toml`
- Audit all imports to ensure no unused dependencies

**Acceptance Criteria:**
- [ ] `pydantic` removed from dependencies
- [ ] All remaining dependencies are actually used
- [ ] Import verification script in CI

**Files to Modify:**
- `pyproject.toml`

---

## Phase 3: Bug Fixes (Week 3)

### 3.1 Fix `move` Command Rollback
**Priority:** 🟠 MEDIUM

**Problem:** If move partially fails (copy succeeds, delete fails), skill exists in both locations with no recovery

**Solution:**
- Implement atomic move with rollback
- If delete fails after copy, attempt to remove copied skill
- Report partial failure clearly

```python
def move_skill(skill, source, target) -> MoveResult:
    try:
        shutil.copytree(skill.path, dest)
    except Exception:
        return MoveResult.FAILED_COPY
    
    try:
        remove_from_source(skill.path)
    except Exception as e:
        # Rollback: remove copied skill
        try:
            shutil.rmtree(dest)
        except:
            pass  # Best effort rollback
        return MoveResult.FAILED_DELETE
    
    return MoveResult.SUCCESS
```

**Acceptance Criteria:**
- [ ] Partial failures are handled gracefully
- [ ] Rollback attempted on failure
- [ ] User informed of exact failure mode
- [ ] Unit tests for partial failure scenarios

**Files to Modify:**
- `skillboard/cli.py`
- `tests/test_move.py` (new comprehensive tests)

---

### 3.2 Fix Orphaned Skill Handling
**Priority:** 🟠 MEDIUM

**Problem:** Skills in target but not source have `path` pointing to target, causing confusion

**Solution:**
- Add explicit `is_orphaned` flag to `Skill` class
- Orphaned skills show warning in TUI
- Provide `cleanup` command to remove orphaned symlinks

**Acceptance Criteria:**
- [ ] Orphaned skills clearly identified
- [ ] User warned about orphaned skills
- [ ] Cleanup command available
- [ ] Unit tests for orphaned skill detection

**Files to Modify:**
- `skillboard/manager.py`
- `skillboard/cli.py` (add `cleanup` command)

---

### 3.3 Fix KeyboardInterrupt vs ImportError Handling
**Priority:** 🟠 MEDIUM

**Problem:** `except (KeyboardInterrupt, ImportError)` treats both the same

**Solution:**
```python
try:
    import inquirer
except ImportError:
    console.print("[red]Error: 'inquirer' package is required.[/red]")
    console.print("Install with: pip install inquirer")
    sys.exit(ExitCode.MISSING_DEPENDENCY)

try:
    answers = inquirer.prompt(questions)
except KeyboardInterrupt:
    console.print("\n[yellow]Cancelled.[/yellow]")
    return None
```

**Acceptance Criteria:**
- [ ] ImportError shows installation instructions
- [ ] KeyboardInterrupt shows "Cancelled" message
- [ ] Different exit codes for different exceptions

**Files to Modify:**
- `skillboard/cli.py`
- `skillboard/tui.py`

---

## Phase 4: Type Safety & Code Quality (Week 4)

### 4.1 Complete Type Hints
**Priority:** 🟢 MEDIUM

**Problem:** Missing type hints, use of `Any`, imports inside functions

**Solution:**
- Add proper type hints to all functions
- Create type aliases for common types
- Move imports to module level where possible

**Type Aliases:**
```python
# skillboard/types.py
from typing import TypeAlias

SkillName: TypeAlias = str
SkillPath: TypeAlias = Path
SkillSet: TypeAlias = set[SkillName]
```

**Acceptance Criteria:**
- [ ] 100% type coverage (verified by mypy)
- [ ] No `Any` types (except where truly necessary)
- [ ] All imports at module level
- [ ] Type aliases for complex types

**Files to Create/Modify:**
- `skillboard/types.py` (new)
- All `.py` files

---

### 4.2 Add Module-Level Console Type Hint
**Priority:** 🟢 LOW

**Solution:**
```python
# At module level
console: Console = Console()
```

**Files to Modify:**
- `skillboard/cli.py`
- `skillboard/tui.py`

---

### 4.3 Code Organization
**Priority:** 🟢 LOW

**Problem:** Some imports inside functions (lazy loading anti-pattern)

**Solution:**
- Move imports to top of files
- Use proper dependency injection if needed
- Add `__all__` exports to modules

**Files to Modify:**
- `skillboard/cli.py`
- `skillboard/tui.py`

---

## Phase 5: Testing (Week 5)

### 5.1 Comprehensive Test Suite
**Priority:** 🔴 CRITICAL

**Current State:** 24 tests
**Target:** 80+ tests, >90% coverage

**Test Categories:**

1. **Unit Tests** (40 tests)
   - Path resolution (10 tests)
   - Skill operations (15 tests)
   - Configuration (10 tests)
   - Error handling (5 tests)

2. **Integration Tests** (30 tests)
   - CLI commands (20 tests)
   - End-to-end workflows (10 tests)

3. **Edge Case Tests** (15 tests)
   - Empty directories
   - Permission errors
   - Concurrent operations
   - Large skill counts

**Acceptance Criteria:**
- [ ] >90% code coverage
- [ ] All edge cases tested
- [ ] Property-based tests for complex logic
- [ ] CI fails if coverage drops

**Files to Create:**
- `tests/test_paths.py`
- `tests/test_cli.py`
- `tests/test_integration.py`
- `tests/test_edge_cases.py`
- `tests/conftest.py` (fixtures)

---

### 5.2 Add Property-Based Tests
**Priority:** 🟡 HIGH

**Solution:**
```python
# tests/test_properties.py
from hypothesis import given, strategies as st

@given(st.sets(st.text(min_size=1, max_size=50), min_size=0, max_size=100))
def test_skill_selection_roundtrip(skills):
    """Selected skills should match what user selected."""
    ...
```

**Acceptance Criteria:**
- [ ] Property tests for skill selection
- [ ] Property tests for path resolution
- [ ] Property tests for content hashing

---

## Phase 6: Documentation (Week 6)

### 6.1 Complete Command Documentation
**Priority:** 🔴 CRITICAL

**Missing Documentation:**
- `copy` command with all flags
- `move` command with all flags
- `read` command
- `--all` flag
- `--dry-run` flag
- `--force` flag
- `--output-scope` and `--input-scope`

**Structure per command:**
```markdown
### `command-name`
Brief description.

**Usage:**
\`\`\`bash
skillboard command-name [OPTIONS]
\`\`\`

**Options:**
- `-i, --input`: Description
- `-o, --output`: Description
- `--all`: Description

**Examples:**
\`\`\`bash
# Example 1
skillboard command-name -i warehouse -o claude

# Example 2 with flags
skillboard command-name -i warehouse -o claude --all
\`\`\`
```

**Acceptance Criteria:**
- [ ] Every command fully documented
- [ ] Every flag documented with examples
- [ ] All examples tested and working
- [ ] Common workflows documented

**Files to Modify:**
- `README.md`
- `docs/commands.md` (new)

---

### 6.2 API Documentation
**Priority:** 🟡 HIGH

**Solution:**
- Add docstrings to all public APIs
- Generate API docs with Sphinx or MkDocs
- Host on ReadTheDocs

**Acceptance Criteria:**
- [ ] All public functions have docstrings
- [ ] API reference generated automatically
- [ ] Examples in docstrings

---

### 6.3 Changelog
**Priority:** 🟡 HIGH

**Create `CHANGELOG.md`:**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features...

### Fixed
- Bug fixes...

## [1.0.0] - YYYY-MM-DD

### Added
- Production release
...
```

---

## Phase 7: Final Validation (Week 6-7)

### 7.1 Pre-Release Checklist

**Code Quality:**
- [ ] All tests passing (100%)
- [ ] Type checking passes (mypy strict)
- [ ] Linting passes (ruff)
- [ ] Code coverage >90%
- [ ] No security vulnerabilities (bandit)

**Documentation:**
- [ ] README accurate and complete
- [ ] All examples tested
- [ ] API docs generated
- [ ] Changelog updated

**Testing:**
- [ ] Manual testing on Linux, macOS, Windows (if applicable)
- [ ] Test with real skill directories
- [ ] Performance test with large skill sets (100+ skills)

**Release:**
- [ ] Version bumped to 1.0.0
- [ ] Git tag created
- [ ] PyPI package published
- [ ] GitHub release notes

---

## Breaking Changes from v0.3.x

The following breaking changes are planned for v1.0.0:

1. **Exit Codes**: Standardized exit codes (may differ from v0.3.x)
2. **Error Messages**: More consistent error message format
3. **Removed**: `sync` command (never existed, but was documented)

---

## Migration Guide (v0.3.x → v1.0.0)

### For Users:

1. **Update scripts using exit codes** if checking specific exit codes
2. **Update documentation references** from `sync` to `link`
3. **No breaking changes** to actual working commands

### For Contributors:

1. **New module structure**: Path resolution moved to `paths.py`
2. **New error handling**: Use `error()` function instead of `print()`
3. **Type hints required**: All new code must be fully typed

---

## Success Metrics

| Metric | v0.3.x | v1.0.0 Target |
|--------|--------|---------------|
| Test Count | 24 | 80+ |
| Code Coverage | ~60% | >90% |
| Type Coverage | ~70% | 100% |
| Documented Commands | 4/7 | 7/7 |
| Known Bugs | 8 | 0 |
| Open Issues | - | 0 critical |

---

## Appendix: Issue Tracker

### Critical Issues (MUST FIX)
- [ ] #1: Version mismatch
- [ ] #2: Non-existent command documented
- [ ] #3: Wrong command examples

### High Priority
- [ ] #4: Code duplication (path resolution)
- [ ] #5: Inconsistent error handling
- [ ] #6: Unused dependencies
- [ ] #7: Incomplete test coverage

### Medium Priority
- [ ] #8: Move command rollback
- [ ] #9: Orphaned skill handling
- [ ] #10: Exception handling clarity
- [ ] #11: Missing type hints

### Low Priority
- [ ] #12: String concatenation style
- [ ] #13: Import organization

---

## Notes

- This plan assumes 1 developer working full-time
- Adjust timeline based on available resources
- Consider releasing v0.4.0 with partial fixes if v1.0.0 takes too long
- All changes should maintain backward compatibility where possible
- Focus on stability over new features for v1.0.0

---

**Document Version:** 1.0
**Last Updated:** 2026-04-15
**Author:** OpenCode Analysis
