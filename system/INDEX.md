# Casper Factory — System Documentation

> **READ THIS FIRST** before any session — scheduled, Cowork, or manual.
> This wiki is the single source of truth for how the entire Casper Factory system works.

## Quick Links

- [ARCHITECTURE.md](system/ARCHITECTURE.md) — Full system map with diagrams. How everything connects.
- [DASHBOARD-LOGIC.md](system/DASHBOARD-LOGIC.md) — Dashboard internals: data.json schema, rendering pipeline, rebuild process.
- [SESSION-CHAIN-LOG.md](system/SESSION-CHAIN-LOG.md) — Rolling chain log of every session. Check before starting work.
- [DONTS.md](system/DONTS.md) — Anti-patterns, guardrails, and change advisory protocol.
- [AI-OPERATING-GUIDE.md](system/AI-OPERATING-GUIDE.md) — Step-by-step guide for AI sessions. Read order, verification, logging.

## File Architecture

```
Dropbox/
├── Brain/                              ← Obsidian vault (cross-project hub, VIEWING layer)
│   └── projects/caspervpn/
│       ├── memory → symlink to Casper-Code/memory
│       └── dashboard → symlink to Dashboard-/system
│
├── app-link/                           ← Project repos (DATA + OPS layers)
│   └── CasperVPN/
│       ├── Code/Casper-Code/           ← Git clone (branch: dropbox-local)
│       │   └── memory/                 ← Vault data written by factory scripts
│       └── Dashboard/Dashboard-/       ← Git clone (branch: main)
│           ├── data.json               ← Dashboard state
│           ├── index.html              ← Live dashboard (INLINE_DATA baked in)
│           └── system/                 ← THIS wiki (you are here)
│
~/Documents/Claude/Scheduled/           ← Scheduled task definitions
    ├── _factory/                       ← Shared Python scripts
    └── casper-{dept}/SKILL.md          ← 11 department workflows

GitHub (remote):
├── oatarabay-app-link/Casper-Code      ← branch: dropbox-local
└── oatarabay-app-link/Dashboard-       ← branch: main
```

## Three-Layer Rule

| Layer | Repo | Location | Purpose |
|-------|------|----------|---------|
| DATA | Casper-Code | `app-link/CasperVPN/Code/Casper-Code/` | Code + memory vault. Factory writes here. |
| OPS | Dashboard- | `app-link/CasperVPN/Dashboard/Dashboard-/` | Dashboard + system docs. Ops reference. |
| VIEW | Brain | `Dropbox/Brain/` | Obsidian vault. Reads via symlinks. Never written to directly. |

## Future Projects

When adding a new project (River Zen, Real Estate, AI Ventures):
1. Create its repo under `app-link/<Project>/Code/<Repo>/` with a `memory/` folder
2. Clone Dashboard/ops repo under `app-link/<Project>/Dashboard/<Repo>/` if it has a dashboard
3. Add symlinks from `Brain/projects/<project>/` to the source repos
4. Same three-layer pattern. No exceptions.

---
*Last updated: 2026-03-11 | Maintained by: CEO + Factory system*
