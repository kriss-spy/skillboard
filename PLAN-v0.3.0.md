# Skillboard v0.3.0 Development Plan

## Critical Fix: Standard Path Correction

**Current (WRONG):** `~/.agent/skills`  
**Correct (STANDARD):** `~/.agents/skills`

This is a **breaking change** that affects all agent paths:
- `~/.agent/skills` → `~/.agents/skills`
- `~/.agent/skill-warehouse` → `~/.agents/skill-warehouse`

**Migration strategy:**
- v0.3.0 will use the new paths
- Add warning for users with old paths
- Migration command: `skillboard migrate` (optional for v0.3.0)

---

## Planned Features

### 1. New `read` Command

**Purpose:** Quick reference for skill content without opening an editor

**Syntax:**
```bash
skillboard read <skill-name>              # Read from default source
skillboard read <skill-name> -a <agent>   # Read from specific agent
skillboard read <skill-name> --local      # Read from local .agents/skills
skillboard read <skill-name> --github     # Read from .github/skills
```

**Output style** (like `openskills read`):
```
┌─────────────────────────────────────┐
│ 3d-web-experience                   │
├─────────────────────────────────────┤
│                                     │
│ Description:                        │
│   Create 3D web experiences using   │
│   Three.js and React Three Fiber    │
│                                     │
│ Author: vercel-labs                 │
│ Version: 1.2.0                      │
│                                     │
│ Files:                              │
│   • SKILL.md                        │
│   • examples/                       │
│   • templates/                      │
│                                     │
└─────────────────────────────────────┘
```

**Implementation:**
- Parse `SKILL.md` if it exists
- Show metadata (description, author, version)
- List files in the skill directory
- Show truncated preview of SKILL.md content (first 20 lines)

**Files to modify:**
- `skillboard/cli.py`: Add `read` command
- May need: `skillboard/skill_reader.py`: Parse SKILL.md

**Estimated effort:** Medium (3-4 hours)

---

### 2. Support for `.github/skills`

**Purpose:** Support skills stored in `.github/skills` directory (common pattern)

**Syntax:**
```bash
skillboard list --github              # List skills in .github/skills
skillboard sync -i github -o claude   # Sync from .github/skills to claude
skillboard read my-skill --github     # Read skill from .github/skills
```

**Behavior:**
- Look for `.github/skills` in current directory
- Treat it like other local skill directories
- Add `github` as a special alias

**Implementation:**
```python
# In config.py or cli.py
github_skills = Path(".github/skills")
if github_skills.exists():
    # Add to available sources
```

**Files to modify:**
- `skillboard/config.py`: Add github path detection
- `skillboard/cli.py`: Add --github flag to relevant commands

**Estimated effort:** Small-Medium (2-3 hours)

---

### 3. Clarify Sync Uses Symlinks

**Current issue:** Users may not realize sync creates symlinks (not copies)

**Solutions:**

**A. Rename command (breaking):**
```bash
skillboard link -i claude -o agent    # Instead of sync
```

**B. Add explicit documentation:**
```bash
skillboard sync --help
# Add: "Creates symbolic links from source to target"
```

**C. Add info message:**
```bash
$ skillboard sync -o claude
Creating symbolic links from ~/.agents/skills to ~/.claude/skills...
```

**D. Add --method flag (future):**
```bash
skillboard sync -o claude --method link    # Default
skillboard sync -o claude --method copy    # Future: actual copy
```

**Recommendation for v0.3.0:** Options B + C (documentation + info message)

**Files to modify:**
- `skillboard/cli.py`: Update help text and add info message
- `README.md`: Clarify symlink behavior

**Estimated effort:** Small (1 hour)

---

## Technical Details

### Symlink Path Type

**Question:** Does sync use relative or absolute path in symlink?

**Answer:** Uses **RELATIVE** paths (line 206 in manager.py):

```python
# Create relative symlink
relative_source = os.path.relpath(source_skill, self.target_path)
target_skill.symlink_to(relative_source, target_is_directory=True)
```

**Why relative?**
- ✅ Portable (works if home directory moves)
- ✅ Works in containerized environments
- ✅ Shorter paths

**Example:**
```
~/.claude/skills/my-skill → ../../.agents/skills/my-skill
```

**Not absolute:**
```
~/.claude/skills/my-skill → /home/user/.agents/skills/my-skill
```

---

## Implementation Schedule

### Week 1: Critical Fix
- [ ] Update default paths from `.agent/` to `.agents/`
- [ ] Update config.py
- [ ] Update documentation
- [ ] Add migration warning

### Week 2: Read Command
- [ ] Implement SKILL.md parser
- [ ] Create read command
- [ ] Add formatted output
- [ ] Write tests

### Week 3: GitHub Skills Support
- [ ] Add .github/skills detection
- [ ] Add --github flag to commands
- [ ] Write tests

### Week 4: Documentation & Polish
- [ ] Clarify symlink behavior in docs
- [ ] Add info messages
- [ ] Update README
- [ ] Write comprehensive tests
- [ ] Release v0.3.0

---

## Breaking Changes

1. **Path change:** `~/.agent/` → `~/.agents/`
   - Affects: warehouse, agent paths
   - Migration: Users need to rename directories or re-init

2. **No other breaking changes planned**

---

## Testing Checklist

- [ ] Path change works correctly
- [ ] Read command displays skill info correctly
- [ ] GitHub skills detection works
- [ ] Symlinks still work after path change
- [ ] All existing tests pass
- [ ] New tests for read command
- [ ] New tests for github skills

---

## Questions

1. Should we provide a migration assistant?
   - `skillboard migrate` command to move `~/.agent/` to `~/.agents/`
   - Or just warn users?

2. For `read` command, what if SKILL.md doesn't exist?
   - Show directory listing only?
   - Show error?

3. Should `.github/skills` be checked recursively up the directory tree?
   - Like git looks for `.git`?
   - Or only in current directory?
