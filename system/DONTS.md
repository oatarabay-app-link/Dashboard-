# System Don'ts & Guardrails

> Anti-patterns that have caused real incidents. Read before every session.

## CRITICAL DON'TS

### 1. Never git clone in factory scripts
- **Why**: Factory scripts use GitHub Contents API for atomic read/write
- **What happens**: Clone creates state conflicts, .git lock files, merge issues
- **Instead**: Use `api_get()` and `api_put()` from factory_bootstrap.py

### 2. Never push data.json without re-baking INLINE_DATA
- **Why**: index.html has an embedded copy of data.json for faster loading
- **What happens**: Live dashboard shows stale data
- **Instead**: Always use `push_dashboard()` which calls `rebuild_dashboard()` automatically

### 3. Never mark tasks green (verified) unless you are CEO
- **Why**: Self-reported completion has no verification
- **What happens**: Tasks appear done but may have bugs
- **Instead**: Mark yellow (self-verified). CEO marks green after testing.

### 4. Never skip Phase 0 (vault sync)
- **Why**: Obsidian Brain vault needs fresh data from GitHub
- **What happens**: Brain shows stale data, CEO makes decisions on old info
- **Instead**: Always run `session_start.py` first — it calls `vault_sync()`

### 5. Never work on another department's code without authorization
- **Why**: Cross-department changes create merge conflicts and break ownership
- **What happens**: Untested changes in unfamiliar code
- **Instead**: Create a handoff task with `dept_handoff_create.py`

### 6. Never merge to main branch
- **Why**: `main` is production. All work happens on `dropbox-local`
- **What happens**: Untested code in production
- **Instead**: All commits to `dropbox-local`. Fixes cherry-picked to `fix/*` from main.

### 7. Never skip Phase 4 (session exit)
- **Why**: Session work is invisible without logging
- **What happens**: CEO can't track progress, next session repeats work
- **Instead**: Always run `dept_exit.py` with a meaningful summary

### 8. Never create crossDeptTasks without all required fields
- **Why**: Missing fields crash the dashboard renderer
- **Required fields**: id, from, to, title, status, priority, createdAt, createdDate
- **Instead**: Always use `create_handoff()` from factory_bootstrap.py

### 9. Never hardcode paths with wrong casing
- **Correct**: `app-link` (lowercase, hyphenated)
- **Wrong**: `AppLink`, `App-Link`, `applink`, `APP-LINK`
- **Why**: macOS is case-insensitive but Linux VMs are not
- **Impact**: Scripts work locally but fail in Cowork/Scheduled sessions

### 10. Never edit index.html INLINE_DATA manually
- **Why**: Must match data.json exactly — manual edits create drift
- **Instead**: Edit data.json, then call `rebuild_dashboard()`

## CHANGE ADVISORY PROTOCOL

Before making ANY structural change to the factory system:

### Pre-Flight Checklist
1. Read `system/ARCHITECTURE.md` — understand the full flow
2. Read `system/DONTS.md` (this file) — check for known anti-patterns
3. Check `DEPARTMENT_LOG.md` — any recent changes that conflict?
4. Check `data.json` crossDeptTasks — any pending work that depends on current structure?
5. Test in isolation — never push untested structural changes

### Change Categories
| Category | Risk | Approval |
|----------|------|----------|
| Data (task status, completion %) | Low | Any department |
| Dashboard rendering (index.html JS) | Medium | CEO or QA |
| Factory scripts (factory_bootstrap.py) | High | CEO only |
| Repository structure (new folders, moved files) | High | CEO only |
| Scheduled task definitions (SKILL.md) | Medium | CEO review |

### Post-Change Verification
1. Dashboard renders correctly (check all 3 sections)
2. `session_start.py` runs without errors
3. `dept_exit.py` logs to all 4 targets
4. vault_sync() finds and updates local clone
5. Brain symlinks still resolve