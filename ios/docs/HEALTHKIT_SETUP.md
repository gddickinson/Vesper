# HealthKit setup (Mindful Minutes + State of Mind)

Vesper can write to Apple Health when the user turns on **Settings ▸ Sync to
Apple Health**:

- a **Mindful Minutes** (`mindfulSession`) sample on every session end ≥ 60 s, and
- on iOS 18+, a **State of Mind** (`HKStateOfMind`) sample from the post-session
  mood check-in (1–5 mapped to valence −1 … +1).

The Swift side is already implemented in `Vesper/Audio/HealthStore.swift` and
wired into `SessionViewModel` (`syncHealth`, the `pause()` write, and the
`logMood` write). **It compiles, links and runs today with no entitlement** —
every call is guarded, so without the capability below it is a silent no-op and
never crashes. To actually persist data you must add three things in Xcode (none
of which can be scripted from the agent because they require the signed project /
entitlements UI):

## Reading heart rate (HRV coherence biofeedback)

The Meditate **Heart coherence** ring (`Audio/Coherence.swift` + `Audio/HeartRateSource.swift`)
can read **live heart rate** to compute a real coherence score. This is **read**
access (separate from the writes above):

- Add `HKObjectType.quantityType(forIdentifier: .heartRate)` to the **read** set in
  `HeartRateSource.startReal` (already coded) — it requests read auth and runs an
  `HKAnchoredObjectQuery` streaming `.heartRate`.
- Requires the same **HealthKit capability** (below) plus `NSHealthShareUsageDescription`.
- Without the entitlement / on the Simulator the auth request simply fails and **no
  real samples stream** — the ring falls back to a **breath-driven demo tachogram**
  (respiratory sinus arrhythmia), so the feature is fully usable and demonstrable
  with no sensor and never crashes.
- Real HR is only requested when the user turns on **Settings ▸ Sync to Apple Health**
  (the same `syncHealth` toggle), and only while a Meditate session is running.
- Best signal comes from an Apple Watch feeding HR into Health in real time.

## 1. Add the HealthKit capability

Target **Vesper ▸ Signing & Capabilities ▸ + Capability ▸ HealthKit**.
This adds `com.apple.developer.healthkit` to `Vesper.entitlements`. You do **not**
need "Clinical Health Records" or background delivery for this write-only use.

## 2. Add the two Info.plist usage strings

Health writes are rejected at runtime without purpose strings. Add to the target's
Info.plist (Info tab, or Info.plist source):

```xml
<key>NSHealthUpdateUsageDescription</key>
<string>Vesper logs your mindful minutes and post-session mood to Apple Health.</string>
<key>NSHealthShareUsageDescription</key>
<string>Vesper uses Apple Health to record your mindfulness sessions.</string>
```

`NSHealthShareUsageDescription` is required by the API even though Vesper only
writes (it does not read). Both must be non-empty or the app is rejected.

## 3. (Capabilities note) State of Mind

`HKStateOfMind` is iOS 18+. The code is already `@available(iOS 18.0, *)`-guarded
and falls back to writing only Mindful Minutes on iOS 17. No extra entitlement
beyond the HealthKit capability is needed.

## How it behaves

- The toggle only appears when `HKHealthStore.isHealthDataAvailable()` is true
  (iPhone; not iPad/Mac Catalyst without Health).
- Turning the toggle **on** calls `requestAuthorization(toShare:)` once — the user
  sees the system Health permission sheet. If they decline, nothing is written and
  nothing breaks (`authorizationStatus(for:)` gates every save).
- Writes are best-effort: the save completion is ignored, so a denied or
  unconfigured Health store simply drops the sample.

## Verifying

After enabling the capability + plist strings on a **real device** (Health is not
fully exercised on Simulator): toggle Sync on, accept the permission sheet, run a
session ≥ 1 min, then check **Health ▸ Browse ▸ Mindfulness** for the minutes and
(iOS 18) **Health ▸ Browse ▸ State of Mind** for the mood entry.
