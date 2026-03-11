# System Architecture

## Overview Diagram

```mermaid
flowchart TB
    subgraph SCHEDULED["Scheduled Tasks (11 depts, every 2h Mon-Fri)"]
        SK[SKILL.md Phase 0-4]
        FS[factory_bootstrap.py]
        SS[session_start.py]
        DE[dept_exit.py]
        DC[dept_check.py]
        HC[dept_handoff_create.py]
        HD[dept_handoff_complete.py]
    end

    subgraph GITHUB["GitHub (Remote)"]
        CR[Casper-Code repo<br/>branch: dropbox-local]
        DR[Dashboard- repo<br/>branch: main]
        GP[GitHub Pages<br/>oatarabay-app-link.github.io/Dashboard-]
    end

    subgraph DROPBOX["Dropbox (Local)"]
        CC[Casper-Code clone<br/>app-link/CasperVPN/Code/Casper-Code/]
        DC2[Dashboard- clone<br/>app-link/CasperVPN/Dashboard/Dashboard-/]
        BR[Brain vault<br/>Dropbox/Brain/]
    end

    subgraph OBSIDIAN["Obsidian"]
        OV[Brain vault viewer]
    end

    SK --> FS
    FS -->|GitHub API read/write| CR
    FS -->|GitHub API read/write| DR
    DR -->|auto-deploy| GP
    FS -->|vault_sync git fetch+reset| CC
    CC -->|symlink| BR
    DC2 -->|symlink| BR
    BR --> OV
```

## Data Flow — Write Path

```mermaid
sequenceDiagram
    participant S as Scheduled Task VM
    participant FB as factory_bootstrap.py
    participant GH as GitHub API
    participant CR as Casper-Code Repo
    participant DR as Dashboard- Repo
    participant VS as vault_sync()
    participant CC as Local Casper-Code Clone
    participant OB as Obsidian Brain

    S->>FB: Phase 3 — dept does work
    S->>FB: Phase 4 — dept_exit.py calls session_exit()
    FB->>GH: Write to memory/departments/<dept>/session-log.md
    FB->>GH: Write to memory/sessions/<date>-factory-sessions.md
    FB->>GH: Write to DEPARTMENT_LOG.md
    FB->>GH: Write to CHANGELOG.md
    FB->>GH: Push data.json to Dashboard-
    FB->>GH: Rebuild index.html with INLINE_DATA
    FB->>VS: vault_sync()
    VS->>CC: git fetch origin + git reset --hard
    CC-->>OB: Obsidian reads via Brain symlink
```

## Data Flow — Read Path

```mermaid
sequenceDiagram
    participant S as Scheduled Task VM
    participant FB as factory_bootstrap.py
    participant GH as GitHub API
    participant VS as vault_sync()
    participant CC as Local Clone

    S->>FB: Phase 0 — session_start.py
    FB->>VS: vault_sync() — sync local clone first
    VS->>CC: git fetch + reset
    FB->>GH: fetch_dashboard() — read data.json
    FB->>GH: api_get() — read DEPARTMENT_LOG, session logs
    S->>FB: Phase 1 — dept_check.py
    FB->>GH: Read dashboard state via API
```

## Technologies by Layer

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Scheduled Tasks | Claude Cowork Scheduled Tasks | Cron-triggered AI sessions |
| Factory Scripts | Python 3 | API orchestration, vault sync |
| GitHub API | GitHub Contents API v3 | Read/write files without git clone |
| Git Sync | Git (fetch + reset) | Keep local clone in sync |
| Dashboard | HTML + Vanilla JS | Single-page dashboard with INLINE_DATA |
| Dashboard Hosting | GitHub Pages | Static hosting, auto-deploy on push |
| Obsidian Vault | Markdown + Symlinks | Cross-project knowledge browsing |
| Storage | Dropbox | File sync across devices |

## vault_sync() — Multi-Strategy

```mermaid
flowchart TD
    A[vault_sync called] --> B{Try host path}
    B -->|exists| C[git fetch + reset at host path]
    B -->|not found| D{Glob VM mounts}
    D -->|found| E[git fetch + reset at VM mount]
    D -->|not found| F[Skip — API still works]
    C --> G[Obsidian updated]
    E --> G
    F --> H[Obsidian updates on next manual sync]
```

Host path: `/Users/omar/Dropbox/app-link/CasperVPN/Code/Casper-Code`
VM mount patterns: `/sessions/*/mnt/*/CasperVPN/Code/Casper-Code`
Timeout: 60 seconds per operation.
Deduplication: Candidates resolved by `os.path.realpath()` before attempting.

## Session Lifecycle — 5 Phases

```mermaid
flowchart LR
    P0[Phase 0<br/>vault_sync] --> P1[Phase 1<br/>dept_check.py]
    P1 --> P2[Phase 2<br/>Load Context]
    P2 --> P3[Phase 3<br/>Do Work]
    P3 --> P4[Phase 4<br/>dept_exit.py]
```

| Phase | Script | What Happens |
|-------|--------|-------------|
| 0 | session_start.py | vault_sync() syncs local clone, then shows dashboard state |
| 1 | dept_check.py | Reads dashboard via API, shows dept status + pending handoffs |
| 2 | (manual) | Load department SKILL + CLAUDE.md + DEPARTMENT_LOG |
| 3 | (work) | Execute tasks, complete/create handoffs via factory scripts |
| 4 | dept_exit.py | session_exit() writes to 4 vault locations + dashboard + vault_sync |

## Cowork vs Scheduled Sessions

| Aspect | Scheduled Task | Cowork Session |
|--------|---------------|----------------|
| Trigger | Cron (every 2h Mon-Fri) | Manual (user opens Cowork) |
| VM | Fresh VM, no persistent state | VM with mounted folders |
| Dropbox access | No (API only) | Yes (mounts available) |
| vault_sync | Tries host path (fails), tries VM mounts (fails), skips | Tries host path, tries VM mounts (succeeds) |
| API access | Always works | Always works |
| Session logging | Same pipeline (dept_exit.py) | Same pipeline (session_exit) |

---
*Last updated: 2026-03-11*
