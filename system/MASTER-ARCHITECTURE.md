# CASPER FACTORY — MASTER ARCHITECTURE & OPERATING RULES

> CEO-approved system blueprint. Every AI session reads this BEFORE doing any work.
> Last verified: 2026-03-11. Do not deviate.

---

## 1. THREE-LAYER RULE

| Layer | Role | Location | Writes? |
|-------|------|----------|---------|
| **Brain** | VIEWING — Obsidian vault, reads via symlinks | `Dropbox/Brain/` | NO |
| **Casper-Code** | DATA — Source code + all memory/logs | `Dropbox/app-link/CasperVPN/Code/Casper-Code/` | YES (GitHub API, branch: `dropbox-local`) |
| **Dashboard-** | OPS — Live dashboard + system wiki | `Dropbox/app-link/CasperVPN/Dashboard/Dashboard-/` | YES (GitHub API, branch: `main`) |

**Data flows UP. Brain never generates data — it only views what Casper-Code and Dashboard- produce.**

---

## 2. FOLDER ARCHITECTURE (VERIFIED, LIVE)

```
Dropbox/
├── Brain/                                    ← OBSIDIAN VAULT
│   ├── projects/
│   │   ├── app-link/INDEX.md                 ← Infrastructure project
│   │   ├── caspervpn/
│   │   │   ├── INDEX.md
│   │   │   ├── memory → ../../../app-link/CasperVPN/Code/Casper-Code/memory
│   │   │   └── dashboard → ../../../app-link/CasperVPN/Dashboard/Dashboard-/system
│   │   ├── river-zen/INDEX.md
│   │   ├── real-estate/INDEX.md
│   │   └── ai-ventures/INDEX.md
│   ├── cross-project/
│   └── daily/
│
└── app-link/                                 ← ALL PROJECTS
    └── CasperVPN/
        ├── Code/
        │   └── Casper-Code/                  ← Git clone (dropbox-local)
        │       ├── CLAUDE.md                 ← Project rules
        │       ├── DEPARTMENT_LOG.md         ← THE canonical cross-dept log
        │       ├── CHANGELOG.md              ← Code changes
        │       ├── FACTORY_PROTOCOL.md       ← Factory workflow
        │       ├── memory/
        │       │   ├── HOME.md
        │       │   ├── glossary.md
        │       │   ├── context/              ← Protocols, credentials, prompts
        │       │   │   ├── credentials.md
        │       │   │   ├── master-protocol.md
        │       │   │   ├── dependency-map.md
        │       │   │   ├── preflight-protocol.md
        │       │   │   ├── department-prompts.md
        │       │   │   ├── obsidian-git-setup.md
        │       │   │   ├── dashboard-verify.md
        │       │   │   └── session-lock.*
        │       │   ├── departments/          ← One folder per department
        │       │   │   ├── admin-panel/session-log.md
        │       │   │   ├── android/session-log.md
        │       │   │   ├── backend/session-log.md
        │       │   │   ├── ceo/session-log.md
        │       │   │   ├── desktop/session-log.md
        │       │   │   ├── devops/session-log.md
        │       │   │   ├── ios/session-log.md + dept-specific notes
        │       │   │   ├── legal/session-log.md
        │       │   │   ├── marketing/session-log.md
        │       │   │   ├── product/session-log.md + product.md
        │       │   │   ├── qa/session-log.md + qa.md
        │       │   │   └── website/session-log.md
        │       │   └── sessions/YYYY-MM-DD-*.md
        │       └── <source code>/
        │
        ├── Dashboard/
        │   └── Dashboard-/                   ← Git clone (main)
        │       ├── index.html                ← Live dashboard
        │       ├── data.json                 ← Task/status data
        │       ├── build_dashboard.py
        │       ├── README.md
        │       └── system/                   ← System wiki (Brain reads via symlink)
        │           ├── INDEX.md
        │           ├── MASTER-ARCHITECTURE.md ← THIS FILE
        │           ├── ARCHITECTURE.md
        │           ├── DASHBOARD-LOGIC.md
        │           ├── SESSION-CHAIN-LOG.md
        │           ├── DONTS.md
        │           └── AI-OPERATING-GUIDE.md
        │
        ├── Archives/                         ← Legacy snapshots, old factory v1
        ├── Business-Plan/
        ├── Design-Assets/
        ├── Marketing/
        └── Payments/
```

---

## 3. SCHEDULED TASKS

```
Documents/Claude/Scheduled/
├── _factory/                     ← Shared scripts
│   ├── factory_bootstrap.py      ← API, session_exit, vault_sync, create_handoff
│   ├── session_start.py          ← Phase 1 loader
│   ├── dept_exit.py              ← Phase 4 wrapper
│   ├── dept_check.py             ← Status checker
│   ├── dept_handoff_create.py
│   └── dept_handoff_complete.py
├── casper-admin-panel/
├── casper-android/
├── casper-backend/
├── casper-desktop/
├── casper-devops/
├── casper-ios/
├── casper-legal/
├── casper-marketing/
├── casper-product/
├── casper-qa/
├── casper-website/
└── casper-session/               ← CEO session bootstrapper
```

---

## 4. SESSION LIFECYCLE (5 PHASES)

```
Phase 0 — VAULT SYNC
  vault_sync() pulls both clones:
    Casper-Code → origin/dropbox-local
    Dashboard-  → origin/main
  Obsidian Brain sees fresh data via symlinks.

Phase 1 — STATUS CHECK
  session_start.py reads:
    data.json → department status, pending handoffs
    DEPARTMENT_LOG.md → recent cross-dept updates
    CHANGELOG.md → recent code changes

Phase 2 — CONTEXT LOAD
  Read CLAUDE.md + department SKILL.md + relevant memory files.

Phase 3 — WORK
  Execute assigned tasks. All code on dropbox-local branch.

Phase 4 — SESSION EXIT
  dept_exit.py calls session_exit() which writes to:
    1. memory/departments/<dept>/session-log.md
    2. memory/sessions/<date>-factory-sessions.md
    3. DEPARTMENT_LOG.md
    4. CHANGELOG.md
  Then: push_dashboard() → rebuild INLINE_DATA → vault_sync()
```

---

## 5. SYNC CHAIN

### Write Path
```
session_exit(dept, summary)
  → write_session_memory() → 3 locations in Casper-Code via API
  → update_changelog() → CHANGELOG.md via API
  → push_dashboard() → data.json + rebuild index.html INLINE_DATA
  → vault_sync() → git pull both local clones
  → Obsidian Brain sees changes via symlinks
```

### Read Path
```
session_start.py
  → vault_sync() → pull both clones
  → fetch_dashboard() → read data.json
  → api_get() → read DEPARTMENT_LOG.md, CHANGELOG.md
  → Display status, handoffs, recent changes
```

### vault_sync() Details
- Syncs TWO clones: Casper-Code (dropbox-local) + Dashboard- (main)
- Tries host path first (`/Users/omar/Dropbox/...`)
- Falls back to VM mount search (`/sessions/*/mnt/*/...`)
- Deduplicates by realpath
- Removes stale .git lock files
- 60-second timeout per git operation

---

## 6. WHAT BELONGS WHERE

### Dashboard- repo (ONLY these):
- `index.html`, `data.json`, `build_dashboard.py`, `README.md`
- `system/*.md` (system wiki)
- **NOTHING ELSE.** No department notes. No logs. No prompts. No code docs.

### Casper-Code memory/ (ALL knowledge):
- `context/` → shared protocols, credentials, department prompts
- `departments/<dept>/` → session logs + department-specific notes
- `sessions/` → date-stamped overviews
- **Rule:** Every department doc lives INSIDE its folder. Never at `departments/` root.

### Brain/ (read-only):
- `projects/<project>/INDEX.md` + symlinks
- **Rule:** Never write data directly to Brain. Only symlinks.

### DEPARTMENT_LOG.md:
- ONE canonical copy at Casper-Code root
- **Never duplicate to Dashboard- or anywhere else.**

---

## 7. data.json SCHEMA (crossDeptTasks)

```json
{
  "id": "xd-NNN",
  "from": "[DEPT]",
  "to": "[DEPT]",
  "title": "string",
  "description": "string",
  "status": "pending|in_progress|completed|blocked|deferred",
  "priority": "P1|P2|P3",    ← REQUIRED (crashes dashboard if missing)
  "createdAt": "ISO8601",
  "createdDate": "YYYY-MM-DD",
  "completedDate": "YYYY-MM-DD|null"
}
```

**After ANY data.json change:** INLINE_DATA must be re-baked via `push_dashboard()` or dashboard shows stale data.

---

## 8. ABSOLUTE DON'TS

1. **Never git clone in factory scripts** → use `api_get()`/`api_put()`
2. **Never push data.json without re-baking INLINE_DATA** → use `push_dashboard()`
3. **Never mark tasks green unless you are CEO** → self-report = yellow
4. **Never skip Phase 0** → Obsidian gets stale data
5. **Never touch another department's code** → create a handoff
6. **Never merge to main in Casper-Code** → all work on `dropbox-local`
7. **Never skip Phase 4** → session becomes invisible
8. **Never create crossDeptTasks without `priority`** → crashes dashboard
9. **Never use wrong path casing** → `app-link` not `AppLink`
10. **Never edit INLINE_DATA manually** → edit data.json, call `rebuild_dashboard()`
11. **Never duplicate DEPARTMENT_LOG.md** → one copy, Casper-Code root
12. **Never put department docs in Dashboard-** → they go in `memory/departments/<dept>/`
13. **Never put loose files at `memory/departments/` root** → inside the dept folder

---

## 9. CHANGE ADVISORY PROTOCOL

Before ANY structural change:

1. Read `system/MASTER-ARCHITECTURE.md` (this file)
2. Read `system/DONTS.md`
3. Check `DEPARTMENT_LOG.md` for conflicts
4. Check `data.json` crossDeptTasks for dependencies
5. Test in isolation before pushing

| Category | Risk | Approval |
|----------|------|----------|
| Task status / completion % | Low | Any department |
| Dashboard rendering (index.html JS) | Medium | CEO or QA |
| Factory scripts (factory_bootstrap.py) | High | CEO only |
| Repo structure (new folders, moved files) | High | CEO only |
| Scheduled task definitions (SKILL.md) | Medium | CEO review |

---

## 10. FUTURE PROJECTS PATTERN

```
app-link/<ProjectName>/
├── Code/<repo-clone>/
│   └── memory/
├── Dashboard/<dashboard-clone>/   (if needed)
│   └── system/
└── <other folders>/

Brain/projects/<project-key>/
├── INDEX.md
├── memory → symlink to Code/<repo>/memory
└── dashboard → symlink to Dashboard/<repo>/system
```

**Where does this blueprint live?**
- Dashboard- repo: `system/MASTER-ARCHITECTURE.md` (canonical)
- Obsidian sees it via: `Brain/projects/caspervpn/dashboard/MASTER-ARCHITECTURE.md`
- Any new project copies this pattern — blueprint stays in Dashboard-/system/

---

## 11. PATH QUICK REFERENCE

| What | Path |
|------|------|
| Project rules | `Casper-Code/CLAUDE.md` |
| Cross-dept log | `Casper-Code/DEPARTMENT_LOG.md` |
| Credentials | `Casper-Code/memory/context/credentials.md` |
| Dept session log | `Casper-Code/memory/departments/<dept>/session-log.md` |
| Dashboard data | `Dashboard-/data.json` |
| Live dashboard | `https://oatarabay-app-link.github.io/Dashboard-/` |
| System wiki | `Dashboard-/system/` |
| Factory scripts | `Documents/Claude/Scheduled/_factory/` |
| Brain entry | `Brain/projects/caspervpn/` |
| This file | `Dashboard-/system/MASTER-ARCHITECTURE.md` |

---

*This is the single source of truth for system architecture. If reality differs from this doc, reality is wrong — fix reality.*
