# CasperVPN Dashboard — Architecture, Rules & Operations

> **Single Source of Truth**: `Casper-Code/dashboard/data.json`
> **Live URL**: https://oatarabay-app-link.github.io/Dashboard-/
> **Last Audit**: 2026-03-04

---

## 1. Architecture

```
Casper-Code/dashboard/
├── data.json                   ← THE source of truth (all departments read/write here)
├── data.json.lock              ← flock(2) lock file for concurrent write safety
├── index.html                  ← CEO Command Center UI (fetches data.json on load)
├── build_dashboard.py          ← Injects data.json into index.html for offline/file:// use
├── DASHBOARD.md                ← THIS FILE — rules, architecture, operations
├── sync-completions.py         ← Recalculates completion + launchCompletion from AC
├── sync-to-github-pages.sh     ← Pushes data.json + index.html to GitHub Pages repo
├── DASHBOARD_UPDATE_GUIDE.md   ← Legacy guide (superseded by this file + safe-write)
├── DEPARTMENT_PROMPTS.md       ← Legacy prompts (superseded by casper-factory/configs/agent-prompts/)
├── ceo_dashboard_v3.html       ← Archive: v3 prototype
├── index.html.bak              ← Archive: pre-v4 backup
└── test.html                   ← Archive: test page
```

### Data Flow

```
Agent writes ──→ safe-json-update ──→ flock(2) ──→ data.json ──→ index.html reads on load
                                                        │
                                                        ├──→ build_dashboard.py (offline embed)
                                                        └──→ git push → GitHub Pages (live site)
```

### How Completion is Calculated

The dashboard UI (`index.html`) computes completion dynamically — it NEVER reads `departments.*.completion` directly.

```javascript
function calcPct(tasks) {
  // For each task: weight × (progress / 100)
  // progress = (passed criteria / total criteria) × 100
  // Result = sum(weighted_scores) / sum(weights) × 100
}
```

**Implication**: The `departments.*.completion` and `departments.*.launchCompletion` fields in data.json are cached snapshots for CLI tools (`casper status`). They MUST be synced after bulk criteria updates:

```bash
python3 dashboard/sync-completions.py --apply
```

---

## 1b. Milestone Scoping System

Every task has a `"milestone"` field that determines which completion scope it belongs to:

| Milestone | Meaning | Included in launchCompletion? |
|---|---|---|
| `"launch"` | Core feature needed for first App Store/Play Store release | YES |
| `"launch-required"` | Launch dependency but not core UX (e.g. IAP, store submission) | NO |
| `"launch-polish"` | Phase 1 nice-to-have (e.g. biometric auth, notifications) | NO |
| `"phase-2"` | Phase 2 feature (e.g. multi-hop, AI server selection) | NO |
| `"phase-3"` | Phase 3 feature (e.g. macOS app, localization) | NO |
| `"phase-5"` | Phase 5 feature (e.g. Apple TV) | NO |

### Two Completion Numbers Per Department

```json
"departments": {
  "ios": {
    "completion": 54,           // ALL 25 iOS tasks (full roadmap)
    "launchCompletion": 79,     // 12 core launch tasks only
    ...
  }
}
```

**iOS Launch Scope (12 tasks, 79%)**:
wireguard-stable, ikev2-stable, openvpn-ios, kill-switch, auto-reconnect,
bandwidth-monitor, server-list-ui, connection-ui, settings-view, profile-view,
auth-complete, split-tunnel

**iOS Full Scope (25 tasks, 54%)**:
All launch + iap-storekit, app-store-submit, multi-hop, ai-server-selection,
macos-app, apple-tv, threat-protection, biometric-auth, dns-customization,
onboarding, localization, password-reset, notifications-system

### Current Snapshot (2026-03-04)

| Department | Launch % | Full % | Launch Tasks | Total Tasks |
|---|---|---|---|---|
| iOS | 79% | 54% | 12 | 25 |
| Backend | 41% | 33% | 9 | 11 |
| DevOps | 51% | 15% | 2 | 5 |
| Website | 67% | 65% | 1 | 2 |
| Legal | 86% | 29% | 2 | 4 |
| Marketing | 62% | 37% | 1 | 2 |
| Product | 50% | 41% | 2 | 3 |
| **OVERALL** | **61%** | **35%** | **29** | **57** |

---

## 2. data.json Schema

```
{
  "lastUpdated": "ISO-8601 timestamp",
  "updatedBy": "[Department Tag]",
  "overall": { "completion": <int>, "totalWeight": <float>, "phase": "..." },
  "departments": {
    "<key>": { "name": "...", "completion": <int>, "launchCompletion": <int>, "status": "active|idle|blocked", "lead": "...", "blockers": [] }
  },
  "tasks": [
    {
      "id": "<unique-slug>",
      "name": "...",
      "owner": "iOS|Backend|DevOps|Android|Desktop|Website|QA|Legal|Marketing|Product",
      "weight": <float>,          // importance score (higher = more impactful)
      "progress": <int 0-100>,    // COMPUTED from acceptanceCriteria
      "milestone": "launch|launch-required|launch-polish|phase-N",
      "status": "descriptive text",
      "blocked": <bool>,
      "blocker": "text or null",
      "phase": <int>,
      "acceptanceCriteria": [
        { "test": "...", "passed": <bool|null>, "verifiedBy": "...", "verifiedAt": "...", "evidence": "..." }
      ]
    }
  ],
  "crossDeptTasks": [
    {
      "id": "xd-###",
      "from": "[DEPT]",
      "to": "[DEPT]",
      "title": "...",
      "description": "...",
      "priority": "P0|P1|P2",
      "status": "pending|in_progress|completed|blocked",
      "created": "ISO-8601",
      "completedAt": "ISO-8601 or null",
      "completedBy": "[DEPT] or null"
    }
  ],
  "benchmarks": [ ... ],
  "importantNotes": [ ... ],
  "aiFeatures": { ... },
  "antiCensorship": { ... },
  "infrastructure": { ... },
  "verificationPolicy": { ... }
}
```

### Key Counts (as of 2026-03-04)

| Metric | Count |
|---|---|
| Total tasks | 57 |
| iOS tasks | 25 |
| Backend tasks | 11 |
| DevOps tasks | 5 |
| Cross-dept tasks | 78 |
| Acceptance criteria | 422 |
| Departments | 10 |
| Benchmarks | 8 |

---

## 3. SAFE WRITE PROTOCOL (MANDATORY)

### Why

Multiple AI agents write to `data.json` concurrently. Without file locking, agent A reads the file, agent B reads the same file, both modify different fields, agent A writes (OK), agent B writes (OVERWRITES agent A's changes). This is a race condition.

### How

All writes go through two utilities that use `flock(2)` mutual exclusion + atomic rename:

**Dashboard updates** (`safe-json-update`):
```bash
# Set a single field (surgical — only touches that path)
safe-json-update "$DASHBOARD" --set-path departments.ios.completion 85
safe-json-update "$DASHBOARD" --set-path departments.ios.status active

# Merge objects (additive — updates existing items by ID, adds new ones)
safe-json-update "$DASHBOARD" --merge '{"crossDeptTasks": [{"id": "xd-080", "from": "[iOS]", "to": "[BACKEND]", "title": "New task", "status": "pending"}]}'

# Raw jq expression (for complex updates)
safe-json-update "$DASHBOARD" '.tasks[] | select(.id == "wireguard-stable") | .progress = 100'
```

**Department log updates** (`safe-log-append`):
```bash
safe-log-append "$DEPT_LOG" iOS "Kill switch verified — all 5 criteria passing"
```

### FORBIDDEN PATTERNS (will cause data loss)

```bash
# NEVER DO THIS — full-file rewrite race condition:
jq '.departments.ios.completion = 85' data.json > tmp && mv tmp data.json

# NEVER DO THIS — unsynchronized append:
echo "## iOS Update" >> DEPARTMENT_LOG.md

# NEVER DO THIS — read-modify-write-all in Python/Node:
data = json.load(open('data.json'))
data['departments']['ios']['completion'] = 85
json.dump(data, open('data.json', 'w'))
```

### Lock Mechanics

- Lock file: `data.json.lock` (same directory)
- Lock type: `LOCK_EX` (exclusive, one writer at a time)
- Timeout: 30 seconds (prevents deadlocks)
- Write pattern: write to `.tmp` → `fsync` → `os.rename()` (atomic on same filesystem)
- Lock scope: held only during the JSON read→modify→write cycle, released before agent triggers

---

## 4. Reporting Rules

### For AI Agents

1. **SESSION START**: Read `data.json` and `DEPARTMENT_LOG.md` before any work
2. **AFTER COMPLETING A TASK**:
   - Update your task's `status` field with descriptive text
   - Set `acceptanceCriteria[].passed = true` for each criterion you've verified
   - Set `progress` = `round((passed_count / total_count) * 100)`
   - RULE: `progress` can ONLY be 100 when ALL criteria have `passed: true`
   - Update `departments.<your_dept>.completion` to match weighted calcPct
   - Set `lastUpdated` to current ISO timestamp
   - Set `updatedBy` to your department tag
3. **CROSS-DEPT HANDOFFS**:
   - Add new cross-dept task via `safe-json-update --merge`
   - Use sequential ID: check highest existing `xd-###` and increment
   - Auto-handoff system (`auto-handoff.py`) will trigger the receiving agent
4. **BLOCKERS**: Set `blocked: true` and `blocker: "description"` on the task. Log to dept log.

### For CEO (Manual Reviews)

- `casper status` — shows all departments from cached completion fields
- `casper phase <n>` — shows tasks in a specific phase
- `casper criteria <task-id>` — shows acceptance criteria for a task
- `casper tasks active` — shows in-progress tasks
- Live dashboard always shows real-time weighted calculation from criteria

### Completion Sync

The `departments.*.completion` fields are snapshots for CLI tools. After bulk updates, sync them:

```bash
# Recalculate and sync all departments (run from Casper-Code root)
python3 -c "
import json, subprocess
SAFE = '$HOME/casper-factory/scripts/safe-json-update'
DASH = 'dashboard/data.json'
with open(DASH) as f: d = json.load(f)
for dk in d['departments']:
    tasks = [t for t in d['tasks'] if t['owner'].lower() == dk.lower()]
    if not tasks: continue
    tw = sum(t.get('weight',1) for t in tasks)
    ws = sum(t.get('weight',1)*(round(sum(1 for c in t.get('acceptanceCriteria',[]) if c.get('passed')==True)/max(len(t.get('acceptanceCriteria',[])),1)*100)/100) for t in tasks)
    pct = round((ws/tw)*100) if tw > 0 else 0
    subprocess.run([SAFE, DASH, '--set-path', f'departments.{dk}.completion', str(pct)], check=True, capture_output=True)
    print(f'{dk}: {pct}%')
"
```

---

## 5. GitHub Pages Deployment

### Current State (NEEDS UNIFICATION)

| Location | Repo | Tasks | Status |
|---|---|---|---|
| `Casper-Code/dashboard/data.json` | Casper-Code | 57 | **Active — source of truth** |
| `Dashboard-/data.json` | Dashboard- (GH Pages) | 40 | **Stale — older snapshot** |

### Unification Plan

The GitHub Pages repo (`Dashboard-`) must be updated to serve the comprehensive `data.json` from Casper-Code. Two approaches:

**Option A — Manual Push** (current):
```bash
# After significant dashboard updates, push to GitHub Pages:
cd ~/Dashboard-   # or wherever the GH Pages repo is cloned
cp ~/Dropbox/app-link/CasperVPN/Code/Casper-Code/dashboard/data.json .
cp ~/Dropbox/app-link/CasperVPN/Code/Casper-Code/dashboard/index.html .
git add data.json index.html
git commit -m "Sync from Casper-Code $(date +%Y-%m-%d)"
git push origin main
```

**Option B — Automated via GitHub Action** (recommended):
Add a GitHub Action to Casper-Code that pushes `dashboard/data.json` + `dashboard/index.html` to the `Dashboard-` repo on every commit that touches `dashboard/`.

---

## 6. File Inventory & Cleanup

### Active Files (KEEP)
- `data.json` — source of truth
- `data.json.lock` — flock lock file
- `index.html` — CEO Command Center v4
- `build_dashboard.py` — offline embed builder
- `DASHBOARD.md` — THIS FILE

### Superseded Files (ARCHIVE/REMOVE)
- `DASHBOARD_UPDATE_GUIDE.md` — replaced by this file + safe-write protocol
- `DEPARTMENT_PROMPTS.md` — replaced by `casper-factory/configs/agent-prompts/*.prompt`
- `ceo_dashboard_v3.html` — old prototype
- `index.html.bak` — old backup
- `test.html` — test artifact

---

## 7. Verification Policy

From `data.json.verificationPolicy`:
- **Self-reported ≠ done**: Agent claims stay 🟡 until CEO tests and marks 🟢
- **P0 tasks**: CEO reviews all acceptance criteria before accepting
- **Criteria are binary**: passed or not. No partial credit.
- **Evidence required**: `verifiedBy`, `verifiedAt`, `evidence` fields on each criterion

---

## 8. Benchmarks

| % | Milestone | Gate |
|---|---|---|
| 35% | iOS TestFlight Ready | Core VPN, 1 protocol, basic UI |
| 55% | iOS App Store Ready | 2 protocols, kill switch, IAP, legal docs |
| 65% | Android Play Store Ready | Feature parity with iOS launch |
| 72% | macOS + Browser Extensions | Desktop coverage |
| 80% | Windows + CasperCloak | DPI evasion, KSA/UAE unblock |
| 88% | Linux + Smart Features | All platforms, multi-hop, Smart DNS |
| 95% | Enterprise Ready | SOC 2, white-label, dedicated IP, 50+ servers |
| 100% | Top 10 VPN Globally | 100+ servers, 24/7 support, $500K+ MRR |
