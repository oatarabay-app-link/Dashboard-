# CasperVPN iOS — Simulator ↔ Device Switching Checklist

> **PURPOSE:** This file is the single source of truth for everything that must be checked, toggled, or verified when switching between iOS Simulator and real device builds. Every Claude session that touches the iOS build MUST read this file first.

---

## CRITICAL RULE

**Never modify `project.pbxproj` via regex or string replacement.** The file has strict brace balancing (`{` must equal `}`). Any imbalance — even by 1 — corrupts the entire project and Xcode shows "no active scheme." Always start from a known-good base, apply surgical single-field changes, and verify brace count before pushing.

---

## 1. BUILD SCRIPT: libwg-go.a (project.pbxproj Shell Script Phase)

**What:** The WireGuard Go native library is pre-built for arm64 (device only). Simulator needs a stub.

| Build Target | Behavior |
|---|---|
| **Device (arm64)** | Copies real 3.5MB `libwg-go.a` from `Packages/wireguard-apple/Sources/WireGuardKitGo/out/` |
| **Simulator** | Compiles a C stub with all 7 WireGuard symbols → archives into `libwg-go.a` |

**Symbols that MUST exist in the stub:**
```c
void wgSetLogger(void *context, logger_fn_t logger_fn);
int wgTurnOn(const char *settings, int32_t tun_fd);
void wgTurnOff(int handle);
int64_t wgSetConfig(int handle, const char *settings);
char *wgGetConfig(int handle);
void wgBumpSockets(int handle);
void wgDisableSomeRoamingForBrokenMobileSemantics(int handle);
const char *wgVersion(void);
```

**Known Pitfalls:**
- `touch libwg-go.a` creates a 0-byte file → linker fails with "File is empty"
- `${CURRENT_ARCH}` is NOT available in shell script build phases → use `${ARCHS%% *}` instead
- Must use `xcrun --sdk iphonesimulator --find clang` for explicit path (avoids rogue local files)
- Must use `xcrun --sdk iphonesimulator --find libtool` for archiving
- Must use `xcrun --sdk iphonesimulator --show-sdk-path` for `-isysroot`
- If a file named `clang` exists in the project directory, it shadows the real compiler → delete it

**File:** `CasperVPN.xcodeproj/project.pbxproj` → `PBXShellScriptBuildPhase` section

---

## 2. DEV BYPASS FLAGS — Must Be FALSE for Device/Production

| Flag | File | Line | Default | Purpose |
|---|---|---|---|---|
| `DEV_BYPASS_AUTH` | `App/AppCoordinator.swift` | 14 | `false` | Auto-authenticates as dev@caspervpn.com |
| `SCREENSHOT_MODE` | `App/AppCoordinator.swift` | 20 | `false` | Resets onboarding + auto-login for screenshots |
| `DEV_BYPASS_LOGIN` | `Features/Auth/AuthViewModel.swift` | 14 | `false` | Skips login validation |
| `DEV_BYPASS_VPN_AUTH` | `Core/Services/ServerService.swift` | 13 | `false` | Returns hardcoded VPN config |
| `DEV_FORCE_OPENVPN_TCP` | `Core/Services/VPNConnectionManager.swift` | 15 | `false` | Forces OpenVPN TCP over auto-selection |
| `KILLSWITCH_SIMULATOR_MODE` | `Core/Services/KillSwitchManager.swift` | ~line 10 | `false` | Fakes kill switch behavior |

**Rule:** ALL flags must be `false` before ANY device build or App Store submission. These are ONLY for simulator/dev iteration.

---

## 3. SIMULATOR AUTO-DETECTION (Code-Level)

These files detect simulator at runtime via `#if targetEnvironment(simulator)`:

| File | What Happens on Simulator |
|---|---|
| `VPNConnectionManager.swift` (line 59) | `isSimulator = true` → all VPN ops become mocks |
| `IKEv2Manager.swift` (line 42) | Skips `NEVPNManager` initialization entirely |
| `OpenVPNManager.swift` (line 27) | Skips `NETunnelProviderManager` entirely |
| `TunnelsManager.swift` (WG package, line 37) | Uses `MockTunnels.createMockTunnels()` instead of real tunnel loading |

**These are automatic.** No action needed when switching — the code handles it. But be aware mock behavior differs from real:
- Simulator VPN "connects" via 2-second timer delay
- Statistics are random (50-200KB/s receive, 10-50KB/s send)
- No real tunnel, no real encryption, no real network change

---

## 4. NETWORK EXTENSION — DEVICE ONLY

| Component | Simulator | Device |
|---|---|---|
| `CasperVPNTunnel` target | Compiles but cannot run | Fully functional |
| `PacketTunnelProvider.swift` | Never invoked | Handles WireGuard/OpenVPN tunnel |
| `NETunnelProviderManager` | Returns empty/mock | Loads real system tunnels |
| `NEVPNManager` | Cannot connect | Full IKEv2/IPSec support |
| Entitlement: `packet-tunnel-provider` | Parsed but non-functional | Required and enforced |

**No toggles needed** — the runtime simply doesn't invoke the extension on simulator.

---

## 5. ENTITLEMENTS & PROVISIONING

| Entitlement | Simulator | Device |
|---|---|---|
| NetworkExtension packet-tunnel | Ignored | Required (provisioning profile) |
| App Groups `group.com.caspervpn.app` | Works (~/Library/Containers) | Works (shared container) |
| Keychain Access Groups | Works (software keychain) | Works (Secure Enclave backed) |
| Apple Sign-In | Works (simulated) | Works (real) |
| Push Notifications (APNs) | Limited | Full (requires cert + device token) |

**When switching to device:** Verify signing identity + provisioning profile in Xcode → Signing & Capabilities. Automatic signing usually handles this.

---

## 6. STOREKIT / IN-APP PURCHASES

| Environment | Behavior |
|---|---|
| Simulator | Uses StoreKit Configuration file (`.storekit`) for sandbox transactions |
| Device (sandbox) | Connects to Apple sandbox servers |
| Device (production) | Real App Store transactions |

**When switching:** Ensure the StoreKit Configuration is selected in the scheme for simulator testing, and deselected for device testing against real sandbox.

---

## 7. KEYCHAIN BEHAVIOR DIFFERENCES

| Aspect | Simulator | Device |
|---|---|---|
| Storage | Clear-text in `~/Library/Developer/CoreSimulator/` | Hardware-encrypted Secure Enclave |
| App Group sharing | Works but less restrictive | Full access control enforced |
| Password reference verify | May behave differently | `verifyConfigurationReference()` works correctly |
| Biometric (Face ID/Touch ID) | Simulated via menu | Real hardware sensor |

**Risk:** Keychain items saved on simulator won't exist on device and vice versa. Auth tokens must be re-fetched after switching.

---

## 8. CONDITIONAL COMPILATION CHECKS

| Check | Files | Notes |
|---|---|---|
| `#if targetEnvironment(simulator)` | VPNConnectionManager, IKEv2Manager, OpenVPNManager, MockTunnels, TunnelsManager, SimulatorCompatibilityHelper | Automatic — no action needed |
| `#if canImport(TunnelKitOpenVPNAppExtension)` | PacketTunnelProvider.swift | Only compiles if TunnelKit is in the project (currently removed) |
| `#if !canImport(WireGuardKit)` | WireGuardStub.swift | Stub only compiles if real WireGuardKit NOT available |
| `#if canImport(Sentry)` | CrashReporter.swift | Crash reporting framework selection |

---

## 9. XCODE CLEAN BUILD CHECKLIST

### Switching Simulator → Device:
```
1. Verify ALL DEV_BYPASS flags are false (Section 2)
2. Verify SCREENSHOT_MODE = false
3. Verify KILLSWITCH_SIMULATOR_MODE = false
4. Delete DerivedData: rm -rf ~/Library/Developer/Xcode/DerivedData/CasperVPN-*
5. Clean Build Folder: Cmd+Shift+K
6. Select real device as build target
7. Verify signing: Xcode → Signing & Capabilities → Team + Profile
8. Build: Cmd+B
9. StoreKit: Remove StoreKit Configuration from scheme if testing real sandbox
```

### Switching Device → Simulator:
```
1. Delete DerivedData: rm -rf ~/Library/Developer/Xcode/DerivedData/CasperVPN-*
   (CRITICAL: old device libwg-go.a is arm64-only, will fail on simulator)
2. Clean Build Folder: Cmd+Shift+K
3. Delete any rogue files: rm -f <project-dir>/clang
4. Select simulator as build target
5. Build: Cmd+B
6. The build script auto-creates stub libwg-go.a for simulator arch
7. VPN features will be mocked (Section 3)
8. StoreKit: Add StoreKit Configuration to scheme if testing purchases
```

---

## 10. COMMON FAILURE MODES

| Symptom | Cause | Fix |
|---|---|---|
| "Library 'wg-go' not found" | Build script failed silently | Check build log for clang/libtool errors |
| "File is empty in libwg-go.a" | Old `touch` approach created 0-byte file | Ensure stub script creates real .a with symbols |
| "invalid arch name undefined_arch" | `${CURRENT_ARCH}` used instead of `${ARCHS}` | Use `${ARCHS%% *}` in build script |
| "no active scheme" | project.pbxproj brace imbalance | Verify `{` count == `}` count before any push |
| Linker error: missing symbols | Stub .a doesn't export all 7 wg* functions | Check stub C file has all 7 function definitions |
| VPN connects but no traffic | DEV_BYPASS flags still true | Set all to false (Section 2) |
| Auth bypassed unexpectedly | DEV_BYPASS_AUTH or SCREENSHOT_MODE true | Set to false |
| "clang: invalid arch" | Rogue `clang` file in project dir | Delete `<project>/clang` |
| Keychain errors after switch | Different keychain databases | Re-authenticate (tokens don't persist across sim/device) |
| Push notifications don't work on sim | APNs requires real device token | Expected — use device for push testing |
| Mock tunnels appear instead of real | Simulator auto-uses MockTunnels | Expected — switch to device for real VPN |
| NetworkExtension won't load | Simulator can't run extensions | Expected — switch to device |
| Signing errors on device | Wrong provisioning profile | Xcode → Signing & Capabilities → verify Team |

---

## 11. PROJECT.PBXPROJ SAFETY RULES

These rules exist because corrupting this file kills the entire Xcode project:

1. **NEVER use regex replacement on the full file** — brace counts must stay balanced
2. **Always read the clean version first**, apply surgical changes, verify braces
3. **Brace verification:** `content.count('{') == content.count('}')` MUST be true
4. **ShellScript escaping:** `\` → `\\`, `"` → `\"`, newline → `\n` (in that order)
5. **Heredoc in shellScript:** The `<< 'EOF'` syntax works but braces inside the heredoc count toward the file total — be aware
6. **Test after every push:** User must `git pull` + clean build to verify
7. **Keep a known-good SHA:** Before any pbxproj edit, record the last working commit SHA as rollback point

**Last known-good pbxproj commit:** `aabf1fe` (before simulator stub edits)

---

## 12. GIT PULL COMMAND (Copy-Paste Ready)

After any remote change, user runs:
```bash
cd ~/Developer/Casper-Code && rm -f .git/index.lock .git/HEAD.lock && git pull origin dropbox-local
```

After switching build target, always:
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/CasperVPN-*
```

---

## VERSION HISTORY

| Date | Change | By |
|---|---|---|
| 2026-03-01 | Created: comprehensive simulator/device switching reference | [iOS] Claude |
