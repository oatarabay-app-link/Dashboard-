# CasperVPN Dashboard — Department Update Guide

## Architecture

The CEO Command Center is a single HTML file (`index.html`) powered by `data.json`.

**52 tasks** with **weighted scoring** — each task has a `weight` (complexity score out of 104.5 total). The overall readiness % is calculated as: `sum(weight × progress) / sum(weight)`.

**Works everywhere**: When served via HTTP, it fetches `data.json` live. When opened via `file://`, it uses inline data. After updating `data.json`, run `python3 build_dashboard.py` to re-inject inline data.

---

## How to Update (MANDATORY for all departments)

After completing any task:

```
1. Read dashboard/data.json
2. Find your task by "id" in the "tasks" array
3. Update: progress (0-100), status (text), blocked (true/false), blocker (text)
4. Update acceptanceCriteria — set passed: true for each criterion you've verified
5. RULE: progress can ONLY be set to 100 when ALL acceptanceCriteria have passed: true
6. Update your department entry in "departments"
7. Set "lastUpdated" to current ISO timestamp
8. Set "updatedBy" to your department tag (e.g., "[iOS]")
9. Run: python3 dashboard/build_dashboard.py
```

### Acceptance Criteria Protocol

Every task has an `acceptanceCriteria` array — a checklist of specific, testable conditions. These are the success criteria that prove production-readiness.

**Rules:**
- A department CANNOT set progress to 100% unless ALL criteria show `"passed": true`
- CEO reviews criteria on all P0 tasks before accepting completion
- If a criterion cannot be tested yet (dependency not ready), document why in the status field
- Criteria are binary: passed or not. No partial credit.

**Example:**
```json
"acceptanceCriteria": [
  { "test": "Connect to WireGuard server, maintain 60s stable connection", "passed": true },
  { "test": "JWT token refresh on 401 without disconnecting tunnel", "passed": false },
  { "test": "Config cached locally — reconnect uses cache, no API call", "passed": false }
]
```

### Example: iOS Completes Kill Switch

Find in tasks array:
```json
{ "id": "kill-switch", "progress": 0, "status": "Not implemented..." }
```

Update to:
```json
{ "id": "kill-switch", "progress": 100, "status": "Implemented via includeAllNetworks + excludeLocalNetworks. Tested on WiFi and cellular." }
```

---

## Cross-Department Task System

When your department needs work from another department, add to `crossDeptTasks` in data.json:

```json
{
  "id": "xd-ios-backend-ikev2-verify",
  "from": "[iOS]",
  "to": "[BACKEND]",
  "title": "Verify IKEv2 config endpoint",
  "description": "Test GET /servers/{id}/ikev2-config returns valid IKEv2 configuration with CA cert, server address, remote ID. iOS needs this to complete IKEv2 integration.",
  "priority": "P0",
  "status": "pending",
  "created": "2026-02-16T22:00:00Z"
}
```

**Receiving department protocol:**
1. On session start, after reading DEPARTMENT_LOG.md, check `crossDeptTasks` in data.json
2. Filter for tasks where `"to"` matches your department tag
3. Pick up `"pending"` tasks — update status to `"in_progress"`
4. On completion, update status to `"completed"` and add resolution notes to description
5. Run `python3 dashboard/build_dashboard.py`

**Statuses:** `pending` → `in_progress` → `completed` (or `blocked`)

This is the closest to "automatic triggering" without a server — each department checks the queue on session start and picks up their tasks.

---

## What Each Department Owns

| Department | Task IDs to Update |
|---|---|
| **[iOS]** | wireguard-stable, ikev2-stable, openvpn-ios, kill-switch, auto-reconnect, iap-storekit, bandwidth-monitor, auth-complete, server-list-ui, connection-ui, settings-view, profile-view, app-store-submit, split-tunnel, multi-hop, ai-server-selection, biometric-auth, dns-customization, onboarding, password-reset, notifications-system, macos-app, apple-tv, threat-protection, localization |
| **[BACKEND]** | backend-api, admin-backend, support-tickets, payments-stripe, caspercloak-deploy, 2fa |
| **[DEVOPS]** | radius-finalize, server-expansion, monitoring-prometheus, ci-cd-pipeline, smart-dns |
| **[ANDROID]** | android-app, android-tv |
| **[DESKTOP]** | windows-app, linux-app, browser-extensions |
| **[WEBSITE]** | website-final, affiliate-program |
| **[LEGAL]** | privacy-policy, tos, no-log-audit, soc2 |
| **[MARKETING]** | aso-metadata, seo-content |
| **[PRODUCT]** | subscription-ui, dedicated-ip, enterprise-whitelabel |

---

## Benchmarks (Readiness Milestones)

| % | Milestone | What it means |
|---|---|---|
| 35% | iOS TestFlight Ready | Core VPN works, 1 protocol stable, basic UI |
| 55% | iOS App Store Ready | 2 protocols, kill switch, IAP, Privacy Policy, ToS |
| 65% | Android Play Store Ready | Android feature parity with iOS launch |
| 72% | macOS + Browser Extensions | Desktop coverage, browser proxy VPN |
| 80% | Windows + CasperCloak | DPI evasion live, KSA/UAE unblocked |
| 88% | Linux + Smart Features | All platforms, multi-hop, Smart DNS |
| 95% | Enterprise Ready | SOC 2, white-label, dedicated IP, 50+ servers |
| 100% | Top 10 VPN Globally | 100+ servers, 24/7 support, $500K+ MRR |

---

## Hosting Options

**Local**: Open `index.html` in any browser (works via file://)

**Server**: Copy to NL server, serve via Nginx with basic auth:
```bash
sudo mkdir -p /var/www/dashboard
sudo cp dashboard/index.html dashboard/data.json /var/www/dashboard/
# Add Nginx location block with auth_basic
```

**Auto-sync**: Run `build_dashboard.py` in CI/CD after any push to `dashboard/data.json`
