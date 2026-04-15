# Skillboard v0.2.0 Development Plan

## Current Behavior Analysis

### How skillboard handles duplicate skill names:
- **Identification**: Skills are identified by directory name only
- **Collision**: If source and target have same skill name, target version wins (shows as enabled)
- **No merge**: No deduplication or conflict resolution for same-named skills from different sources
- **Orphan tracking**: Skills in target but not source are tracked as "orphaned"

## Planned Features

### 1. Enhanced `skillboard list-path` with Skill Count

**Current behavior:**
```
Alias      Path                          Exists
claude     ~/.claude/skills              ✓
```

**Desired behavior:**
```
Alias      Path                          Exists  Skills
claude     ~/.claude/skills              ✓       64
agent      ~/.agent/skills               ✓       0
warehouse  ~/.agent/skill-warehouse      ✓       0
```

**Implementation:**
- Add skill counting logic to `list-path` command
- Count non-hidden directories in each path
- Show "N/A" or "-" for non-existent paths
- Cache counts? (probably not needed for v0.2.0)

**Files to modify:**
- `skillboard/cli.py`: `list_path()` function
- `skillboard/manager.py`: May need helper method to count skills

**Estimated effort:** Small (1-2 hours)

---

### 2. Compact `skillboard sync` Output

**Problem:** Full table is overwhelming when there are 50+ skills

**Current behavior:**
- Shows full Rich table with all skills
- Columns: Status, Name, Type
- Takes entire terminal screen

**Desired behavior options:**

**Option A: Summary mode (default)**
```
Found 64 skills in ~/.claude/skills
  12 enabled → ~/.agent/skills
  52 available

Select skills to enable/disable...
```

**Option B: Compact list**
```
Skills (64 total, 12 enabled):
  ✓ skill-a    ✓ skill-b    ✓ skill-c
  ✗ skill-d    ✗ skill-e    ✗ skill-f
  ... and 58 more (use --verbose to see all)
```

**Option C: Paginated/grouped view**
- Show first 20 skills
- "... and 44 more"
- Allow pagination with keys

**Recommended:** Option A - Summary mode by default, add `--verbose` flag for full table

**Implementation:**
- Add `--verbose` flag to sync command
- Default: show summary only
- Summary: Total count, enabled count, available count
- Then proceed to inquirer checkbox (which is the important part)

**Files to modify:**
- `skillboard/cli.py`: `sync()` function
- `skillboard/tui.py`: Add summary display, modify skill list display

**Estimated effort:** Medium (3-4 hours)

---

### 3. New `skillboard move` Command

**Purpose:** Move skills between locations (like sync but removes from source)

**Syntax:**
```bash
# Move from global claude to global agent
skillboard move -i claude -o agent

# Move from local claude to global agent  
skillboard move -i claude --input-scope local -o agent

# Move from global claude to local agent
skillboard move -i claude -o agent --output-scope local
```

**Behavior:**
1. Show checkbox menu (same as sync)
2. User selects skills to move
3. Copy skills to target
4. Remove skills from source
5. Confirm before destructive operation

**Safety considerations:**
- Confirm dialog: "This will permanently delete skills from [source]. Continue?"
- Show what will be moved before confirmation
- Error handling: if copy fails, don't delete from source
- Handle conflicts: if skill exists in target, ask to overwrite/skip

**Implementation details:**
- Similar to `sync` but with actual copy+delete instead of symlink
- Need atomic-ish operation: copy first, then delete only if copy succeeds
- Handle partial failures gracefully

**Files to create/modify:**
- `skillboard/cli.py`: New `move()` command
- `skillboard/manager.py`: Add `move_skill()` method

**Estimated effort:** Medium-Large (4-6 hours)

---

## Architecture Considerations

### Duplicate Skill Name Handling

**Current state:** No special handling, last-one-wins

**For v0.2.0:** Content-based deduplication

**Problem:** Two skills with same name might be completely different
- `~/.claude/skills/my-tool` (skill for Claude)
- `./.claude/skills/my-tool` (different skill, same name)

**Solution: Content-based identity**
- Calculate content hash (SHA256) of skill directory
- Two skills are "the same" only if **both** name AND content match
- Different content = different skills (even with same name)

**Implementation:**
```python
def get_skill_content_hash(skill_path: Path) -> str:
    """Calculate hash of all files in skill directory."""
    # Hash all files, sorted by path
    # Return combined hash

def are_skills_identical(skill1: Path, skill2: Path) -> bool:
    """Check if two skill directories have identical content."""
    return get_skill_content_hash(skill1) == get_skill_content_hash(skill2)
```

**In `sync` and `move`:**
- If same name but different content → Treat as different skills
- Show both in list with source indicator:
  ```
  my-tool (global) ✓
  my-tool (local)  ✗
  ```
- Or prefix: `my-tool@global`, `my-tool@local`

**In `move` with conflicts:**
- If target has same name + same content → "Already exists, skipping"
- If target has same name + different content → "Conflict: different content"
  - Options: Skip, Overwrite, Rename

**Practical Example:**
```bash
# Global has my-tool v1.0
~/.claude/skills/my-tool/SKILL.md  # Content: "name: my-tool\nversion: 1.0"

# Local has my-tool v2.0 (different content)
./.claude/skills/my-tool/SKILL.md  # Content: "name: my-tool\nversion: 2.0"

$ skillboard sync -i claude --all -o agent
Found 2 versions of 'my-tool':
  1. my-tool@global (hash: abc123) - version 1.0
  2. my-tool@local  (hash: def456) - version 2.0

Select which to enable (or enable both with different names):
  [ ] my-tool@global
  [x] my-tool@local
  [ ] Rename local to: my-tool-v2

# After sync to agent:
~/.agent/skills/my-tool → symlink to ./.claude/skills/my-tool
```

---

## Development Schedule

### Phase 1: Foundation (Week 1)
- [ ] Implement skill counting in list-path
- [ ] Add `--verbose` flag to sync
- [ ] Create summary display mode
- [ ] Update documentation

### Phase 2: Move Command (Week 2)
- [ ] Design move command interface
- [ ] Implement move logic (copy + delete)
- [ ] Add safety confirmations
- [ ] Handle edge cases (partial failures, conflicts)
- [ ] Write tests

### Phase 3: Polish & Release (Week 3)
- [ ] Improve duplicate skill handling
- [ ] Add more comprehensive tests
- [ ] Update README with new features
- [ ] Create v0.2.0 release
- [ ] Update CHANGELOG

---

## Testing Plan

### Unit Tests Needed
1. Skill counting accuracy
2. Summary display formatting
3. Move command with various scenarios
4. Duplicate detection
5. Error handling in move (partial failures)

### Integration Tests
1. Full sync workflow with many skills
2. Move between different scopes (global↔local)
3. Edge cases: moving to same location, non-existent skills

---

## Breaking Changes

**None planned** - all changes are additive:
- list-path adds a column (not breaking)
- sync adds --verbose flag (default behavior changes slightly, but for better UX)
- move is a new command

---

## Questions to Resolve

1. **Should move be atomic?** (copy all, then delete all - vs - copy-delete one by one)
   - Suggestion: Copy all first, then delete all. If any copy fails, abort without deleting.

2. **What happens if target skill exists?**
   - Options: Skip, Overwrite, Rename (skill-name-1), Ask
   - Suggestion: Ask interactively, with `--force` flag to auto-overwrite

3. **Should we support dry-run for move?**
   - Suggestion: Yes, add `--dry-run` flag to show what would be moved without doing it

4. **Undo capability?**
   - Suggestion: Not for v0.2.0. Users can move skills back manually if needed.

---

## Success Criteria

- [ ] `list-path` shows skill counts
- [ ] `sync` with 100+ skills doesn't flood the terminal
- [ ] `move` command works reliably with proper safety checks
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped to 0.2.0
