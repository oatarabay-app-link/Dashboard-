# iOS Session Log — 2026-04-02
## XD-319: TunnelKit to OpenVPNAdapter Migration

**Operator:** CEO + iOS Cowork Session
**Branch:** dropbox-local
**Status:** Build fixes in progress

---

### Migration Summary
- Removed: TunnelKit (arm64e incompatible with iOS 26 SDK)
- Added: OpenVPNAdapter v0.8.0 via SPM
- New file: CasperVPNTunnel/OpenVPNHandler.swift (delegate-based handler)
- Modified: PacketTunnelProvider.swift (removed TunnelKit, uses OpenVPNHandler)
- Modified: CasperVPN.xcodeproj/project.pbxproj (TKOPENVPN refs replaced with OVPNADAPT)

---

### CRITICAL: OpenVPNAdapter 0.8.0 API Reference

| Property | Wrong (TunnelKit) | Correct (0.8.0) |
|----------|-------------------|-----------------|
| Transport proto | forcedTransportProtocol | configuration.proto |
| TCP/UDP enums | .TCP / .UDP | .TCP / .UDP (NS_ENUM caps) |
| EKU check | checksEKU | DOES NOT EXIST |
| Remote port | String? | UInt (not optional) |
| Connect | connect(using: nil) | connect(using: packetFlow) - NOT optional |
| Byte stats | UInt64 | NSInteger (Int) - cast if needed |
| Packet flow | Automatic | Need: extension NEPacketTunnelFlow: OpenVPNAdapterPacketFlow {} |

### Full OpenVPNConfiguration Properties
- fileContent: Data?, settings: [String: String]?, server: String?, port: UInt
- proto: OpenVPNTransportProtocol (.UDP, .TCP, .adaptive, .default)
- connectionTimeout: Int (0 = infinite), tunPersist: Bool
- googleDNSFallback: Bool, synchronousDNSLookup: Bool
- autologinSessions: Bool, retryOnAuthFailed: Bool, disableClientCert: Bool
- compressionMode: OpenVPNCompressionMode
- privateKeyPassword: String?, keyDirection: Int
- minTLSVersion, tlsCertProfile, sslDebugLevel: Int
- NO checksEKU property exists

### Build Issues and Fixes

**Issue 1: Missing SPM packages after pbxproj edit**
Cause: External pbxproj edit corrupted SPM cache
Fix: rm -rf ~/Library/Caches/org.swift.swiftpm ~/Library/org.swift.swiftpm ~/Library/Developer/Xcode/DerivedData && xcodebuild -resolvePackageDependencies

**Issue 2: Sentry download timeout**
Fix: Retry resolve - transient CDN issue

**Issue 3: 100+ scope errors (Cannot find self)**
Cause: Stray #endif left after replacing #if canImport(TunnelKitOpenVPNAppExtension) block
Fix: Replace orphaned #endif with } to close else branch
Prevention: When replacing #if/#else/#endif blocks, remove ALL three directives together

**Issue 4: 8 API mismatch errors**
Cause: Guessed API names from TunnelKit conventions
Fixes: forcedTransportProtocol->proto, remove checksEKU, fix remotePort type, connect(using: packetFlow), cast stats to UInt64, add NEPacketTunnelFlow extension

**Issue 5: Linker errors (undefined SCNetworkReachability + UIDevice)**
Cause: OpenVPNAdapter requires SystemConfiguration.framework and UIKit.framework
Fix: Add both frameworks to CasperVPNTunnel target in pbxproj (FBP002 build phase)
IDs: SYSCFG001/SYSCFG002 (SystemConfiguration), UIKIT001/UIKIT002 (UIKit)

### pbxproj Reference IDs
- OVPNADAPT01: XCRemoteSwiftPackageReference (repo URL, v0.8.0)
- OVPNADAPT02: Product dep in CasperVPN app
- OVPNADAPT03: Product dep in CasperVPNTunnel
- TNL004/SRC096: OpenVPNHandler.swift build file/ref
- SYSCFG001/SYSCFG002: SystemConfiguration framework (file ref / build file)
- UIKIT001/UIKIT002: UIKit framework (file ref / build file)
- Removed: TKOPENVPN01-04

### Architecture
- OpenVPNHandler: delegate-based, NOT NEPacketTunnelProvider subclass
- PacketTunnelProvider owns OpenVPNHandler via var openVPNHandler
- #if canImport(OpenVPNAdapter) guards with stub fallback
- TCP/UDP: pre-processes .ovpn string (proto + port swap) before adapter
