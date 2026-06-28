# Widgets, Live Activities & Control Center — hand-off

These three platform integrations are the highest-leverage remaining items from
the roadmap (see the `vesper-ios-feature-roadmap` memory). They are **not added in
this round** because each one requires a *new app-extension target* and an *App
Group*, which can only be created through the Xcode target editor / signing UI —
they cannot be generated from source files alone the way the in-app Swift files
are (the main app uses `PBXFileSystemSynchronizedRootGroup`, so loose `.swift`
files auto-compile, but an extension is a separate bundle + target). This document
is the implementation hand-off so it can be done in one focused Xcode session.

## Shared prerequisite: an App Group

All three read Vesper's state from outside the app process, so first add an **App
Group** (e.g. `group.com.georgedickinson.vesper`) to the main target *and* each
extension, then mirror the handful of values the widgets need into a shared
`UserDefaults(suiteName:)` from `SessionViewModel` (streak, this-month minutes,
last-session date, and — for a Live Activity — the running session's end date).
Today everything is in `UserDefaults.standard` / `PracticeLog`; moving the few
widget-facing keys to the suite is the only app-side change.

## 1. Home / Lock-Screen widgets (WidgetKit)

- **Target:** File ▸ New ▸ Target ▸ *Widget Extension* (uncheck "Include Live
  Activity" here; do it as its own target or together — see §2).
- **Content:** a `TimelineProvider` that reads the App-Group defaults and renders:
  - a **streak ring** (current streak + this-month minutes) — `.systemSmall`,
  - a **quick-start** widget whose tap deep-links into a mode. Reuse the existing
    `StartVesperSession` App Intent (in `Vesper/Intents/VesperIntents.swift`) as
    the widget's `AppIntent` so an **interactive widget** (iOS 17+) starts a
    session with no app launch.
- **StandBy / Lock Screen:** add `.accessoryRectangular` / `.accessoryCircular`
  families for the night-stand streak view.
- Refresh cadence: `WidgetCenter.shared.reloadAllTimelines()` from the app after
  `pause()` logs a session; otherwise a daily timeline is plenty (no backend).

## 2. Live Activity + Dynamic Island (ActivityKit)

- **Target:** the Widget Extension with "Include Live Activity" checked, plus
  `NSSupportsLiveActivities = YES` in the **main app** Info.plist.
- **Model:** an `ActivityAttributes` with a static `patternName`/`mode` and a
  `ContentState` carrying the session's `endDate` (and optional phase label).
- **In-session timer with no backend:** render the countdown with
  `Text(timerInterval: now...endDate, countsDown: true)` — it ticks on-device
  with no push updates. Start the Activity in `beginSession()` (when
  `sessionMinutes > 0`) and `end(...)` it in `pause()` / auto-stop. Phase changes
  can `update(...)` the activity, but keep updates sparse (battery).
- Dynamic Island: compact = breath-phase glyph + remaining; expanded = pattern +
  ring. All offline.

## 3. Control Center control / Action Button (iOS 18 `ControlWidget`)

- **Target:** same Widget Extension. Add a `ControlWidget` whose
  `ControlWidgetButton` fires the existing `StartVesperSession` App Intent — a
  one-tap "start a resonance session" Control Center toggle / Action Button
  assignment, zero setup, fully offline.

## Why these are deferred, concretely

Creating a target writes new `PBXNativeTarget` / build-phase / embed-extension
entries into `project.pbxproj` — the one file that is intentionally pinned with
`git update-index --skip-worktree` and must not be machine-edited in this repo.
Do these in Xcode, commit the pbxproj deliberately, then the widget/activity
Swift can live in the new target's group. The app-side glue (App-Group mirror +
`reloadAllTimelines()` + `Activity` start/end in the VM) is small and can be added
to `SessionViewModel` once the targets exist.
