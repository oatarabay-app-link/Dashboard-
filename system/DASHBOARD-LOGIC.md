# Dashboard Logic & Data Schema

> How data.json powers the live dashboard, how it gets updated, and known failure patterns.

## data.json Schema

```json
{
  "lastUpdated": "2026-03-11T...",
  "departments": {
    "<dept_key>": {
      "status": "active|idle|blocked|disabled",
      "completion": 0-100,
      "launchCompletion": 0-100,
      "currentTask": "string",
      "blockers": "string|none"
    }
  },
  "crossDeptTasks": [
    {
      "id": "xd-NNN",
      "from": "[DEPT]",
      "to": "[DEPT]",
      "title": "string",
      "description": "string",
      "status": "pending|in_progress|completed|blocked|deferred",
      "priority": "P1|P2|P3",
      "createdAt": "ISO8601",
      "createdDate": "YYYY-MM-DD",
      "completedDate": "YYYY-MM-DD|null"
    }
  ],
  "importantNotes": ["string or {note, date, dept}"],
  "timeline": [{"date","event","dept"}]
}
```

## REQUIRED FIELDS — Every crossDeptTask MUST have:
| Field | Type | Default | Crash if missing? |
|-------|------|---------|-------------------|
| id | string | auto-gen | No (renders blank) |
| priority | string | "P2" | **YES** — TypeError in renderXDept() |
| status | string | "pending" | No (renders blank) |
| title | string | "" | No |

## Rendering Pipeline

```mermaid
graph LR
    A[data.json on GitHub] -->|GitHub Pages serves| B[index.html loads]
    B -->|INLINE_DATA fallback| C[JavaScript parses]
    C -->|renderXDept\(\)| D[Cross-Dept Section]
    C -->|renderDepts\(\)| E[Department Cards]
    C -->|renderTimeline\(\)| F[Timeline]
```

### INLINE_DATA Bake Process
`rebuild_dashboard()` in factory_bootstrap.py:
1. Reads data.json from GitHub
2. JSON.dumps with indent=2
3. Replaces `const INLINE_DATA = ...;` line in index.html
4. Pushes updated index.html back to GitHub

**CRITICAL**: After ANY data.json change, INLINE_DATA must be re-baked or the live site shows stale data.

## Known Crash Patterns

### 1. Missing `priority` Field (FIXED 2026-03-11)
- **Symptom**: Cross-dept section renders "No cross-department tasks queued"
- **Root cause**: `t.priority.toLowerCase()` throws TypeError on undefined
- **Fix applied**: Null-safe fallback `(t.priority||'P2').toLowerCase()`
- **Prevention**: `create_handoff()` now includes `priority` param (default P2)

### 2. Stale INLINE_DATA
- **Symptom**: Dashboard shows old data despite data.json being updated
- **Root cause**: index.html INLINE_DATA not re-baked after data.json push
- **Fix**: Always use `push_dashboard()` which auto-calls `rebuild_dashboard()`

### 3. GitHub Pages Cache (10min)
- **Symptom**: Push confirmed but live site unchanged
- **Root cause**: GitHub Pages cache-control: max-age=600
- **Fix**: Wait 10 minutes or hard-refresh (Ctrl+Shift+R)

## Update Flows

### Factory Script Updates (Automated)
```
dept_check.py → reads data.json (no write)
dept_exit.py → session_exit() → push_dashboard() → rebuild_dashboard()
dept_handoff_create.py → create_handoff() → push_dashboard()
dept_handoff_complete.py → complete_handoff() → push_dashboard()
```

### Manual/CEO Updates
Edit data.json directly via GitHub web UI or API, then ensure INLINE_DATA is re-baked.