# Session Chain Log

> Append-only rolling log of every factory session. One file per month.
> Location: `system/sessions/YYYY-MM-sessions.md`

## Format

```markdown
## [YYYY-MM-DD HH:MM] DEPT — Summary
- **Phase reached**: 0-4
- **Tasks completed**: [xd-NNN, xd-NNN]
- **Tasks created**: [xd-NNN]
- **Blockers hit**: none | description
- **Files changed**: list of key files
- **Handoffs**: DEPT → DEPT: description
- **Duration**: ~Xmin
- **Session type**: scheduled | cowork
```

## Rules
1. **Append-only** — never edit past entries
2. **One entry per session** — dept_exit.py auto-logs to DEPARTMENT_LOG.md and memory vault
3. **Monthly rollover** — start new file on the 1st of each month
4. **Chain integrity** — each entry references the previous entry's timestamp
5. **CEO review** — CEO sessions should note which dept work was verified

## Reading the Log
- Most recent entries are at the bottom of each monthly file
- Search by department: `grep "## \[.*\] DEVOPS" system/sessions/*.md`
- Search by task ID: `grep "xd-167" system/sessions/*.md`

## Auto-Logging Integration
`session_exit()` in factory_bootstrap.py writes to 4 locations:
1. `memory/departments/<dept>/session-log.md` — per-department detail
2. `memory/sessions/<date>-factory-sessions.md` — daily factory overview
3. `DEPARTMENT_LOG.md` — cross-department communication
4. `CHANGELOG.md` — code-level changes

The chain log in `system/sessions/` is the 5th location, maintained manually or by future automation.