# NVDA Linux Port Plan (Working)

This file tracks Linux port progress in this checkout, what is next, and practical development notes.

## Assumptions and Target Constraints

- Primary target: modern Linux desktops with Wayland and X11 support.
- Accessibility API target: AT-SPI2 (ATK/AT-SPI over D-Bus).
- GUI toolkit: keep wxPython where feasible, with Linux-specific integration updates.
- Speech output: eSpeak NG and Speech Dispatcher first.
- Braille output: brltty/brlapi first.
- Packaging target: Flatpak primary, .deb/.rpm secondary.
- Release standard: smooth daily-use Linux screen reader behavior with
  equivalent Linux execution for existing Windows keyboard shortcuts wherever
  the operating system exposes the required capability.

## Completed So Far

### Phase 0: Baseline Inventory and Guardrails

- CI gate draft created for Linux-port branch (`.github/workflows/linuxPortGate.yml`).
- Target distro set documented (`documentation/nvda linux documentation/dev/target-distro-set.md`).
- Windows-only dependency map documented (`documentation/nvda linux documentation/dev/windows-only-dependency-map.md`).
- Compatibility matrix documented (`documentation/nvda linux documentation/dev/compatibility-matrix.md`).

### Phase 1: Platform Abstraction Layer (PAL)

- PAL package scaffolded under `source/platform/`:
  - `source/platform/common/*`
  - `source/platform/windows/*`
  - `source/platform/linux/*`
  - `source/platform/pal.py`
- Core routed through PAL in `source/core.py` for accessibility/input/session/windowing hooks.
- Linux stubs added for non-implemented capabilities with explicit "not supported yet" behavior.
- Phase 1 status docs added:
  - `documentation/nvda linux documentation/dev/phase-1-pal-foundation.md`
  - `documentation/nvda linux documentation/dev/phase-1-platform-abstraction-layer.md`

### Phase 2 (Initial Slice): AT-SPI2 Foundation

- Added Linux AT-SPI backend scaffold:
  - `source/platform/linux/atspi_backend.py`
- Added AT-SPI role/state mapping helpers:
  - `source/platform/linux/atspi_mappings.py`
- Wired Linux accessibility adapter to backend lifecycle:
  - `source/platform/linux/accessibility.py`
- Added mapping unit tests:
  - `tests/unit/test_linuxAtspiMappings.py`
- Added Phase 2 status doc:
  - `documentation/nvda linux documentation/dev/phase-2-atspi-foundation.md`

- Added translated event dispatch, bounded coalescing, Linux NVDA object wrappers, basic object tree navigation, geometry, and AT-SPI-backed TextInfo primitives.

### Phase 3 (Initial Slice): Input Foundation

- Added normalized Linux keyboard event and `kb:` gesture handoff in:
  - `source/platform/linux/input.py`
- Wired Linux keyboard gesture execution into NVDA `inputCore`.
- Added manual test injection plus X11/Wayland event-source boundaries.
- Added Linux NVDA modifier normalization, held-modifier tracking, double-press pass-through, unbound-command pass-through, and explicit local-only fallback status.
- Added Windows-compatible Linux Super, navigation, and keypad aliases so the existing NVDA keyboard command maps are reused without a separate Linux shortcut table.
- Added Linux input unit tests:
  - `tests/unit/test_linuxInput.py`
- Added Phase 3 status doc:
  - `documentation/nvda linux documentation/dev/phase-3-input-foundation.md`

### Phase 4 (Initial Slice): Speech Foundation

- Added Linux command-backed speech transport:
  - Speech Dispatcher through `spd-say` first.
  - `espeak-ng` command fallback.
- Added discoverable `linuxSpeech` synth driver and Linux-specific automatic synth priority.
- Preserved the existing Windows automatic synth priority.
- Guarded early Windows-only helper/audio startup on Linux and made pending mouse/touch hooks non-fatal during Linux bring-up.
- Added non-fatal Linux DPI/session fallbacks and a lifecycle-compatible Linux message-window placeholder.
- Added a Linux watchdog compatibility module, non-fatal Linux system/windowing defaults, and skipped Win32 desktop cache initialization on Linux.
- Skipped optional Windows-heavy app-module, hardware I/O, braille, vision, display-model, remote, and update initialization during early Linux `0.1` bring-up.
- Added `tools/runLinuxPortPreflight.py` to report Linux desktop, AT-SPI2, wxPython, speech-command, and pending global-keyboard-capture status.
- Added `tools/runLinuxPort.py`, an early Linux launcher that runs preflight, avoids `source/nvda.pyw`, and reports the first remaining core import blocker.
- Added dependency-light Linux speech transport and synth-driver tests.
- Added Phase 4 status doc:
  - `documentation/nvda linux documentation/dev/phase-4-speech-foundation.md`

### Linux Preview Bring-Up

- Added Linux-native launcher and dependency preflight:
  - `tools/runLinuxPort.py`
  - `tools/runLinuxPort.sh`
  - `tools/runLinuxPortPreflight.py`
- Added user-level preview packaging:
  - `packaging/linux/*`
- Added Linux shared-bootstrap fallbacks for logging, localization, registry,
  config, add-on decoding, and queue watchdog selection.
- Added Linux-local AT-SPI object base to avoid loading the shared Windows-heavy
  object stack during native backend construction.
- Added dependency-light document navigation primitives for line movement and
  quick navigation categories.
- Added release-readiness audit:
  - `documentation/nvda linux documentation/dev/linux-preview-release-readiness.md`
- Added full user-release roadmap:
  - `documentation/nvda linux documentation/dev/linux-user-release-roadmap.md`
- Added shortcut-parity audit:
  - `tools/runLinuxShortcutParityAudit.py`
- Added dependency-light Windows and native Ubuntu CI coverage plus an Ubuntu
  preview packaging smoke.
- Added native preview `NVDA+1` input help, `NVDA+F2` pass-next-key-through,
  and `NVDA+F12` date/time parity commands.

## Next Phase Work (Immediate)

### Phase 3: Input and Focus Infrastructure

1. Validate X11 command suppression and pass-through replay on real desktops,
   then deepen the backend where parity gaps remain.
2. Define and implement a Wayland-compatible capture strategy.
3. Add Linux Sticky Keys latch/lock handling and secure global-hotkey behavior.
4. Drive the shortcut-parity audit toward executable shared-runtime coverage.

### Phase 2 Follow-Up

1. Deepen AT-SPI object creation integration with existing NVDA object flows.
2. Extend TextInfo formatting and embedded-object handling.
3. Validate review and browse-mode parity on a real Linux desktop.

### Linux Preview Follow-Up

1. Port shared startup far enough to execute the existing global command map
   instead of relying on the small native preview controller.
2. Replace command-backed speech and audio with persistent Speech Dispatcher
   and streaming PipeWire/Pulse/ALSA paths.
3. Add brlapi-backed braille, Linux device discovery, touch, and richer mouse
   behavior.
4. Add production Flatpak, `.deb`, and `.rpm` packaging after the runtime
   dependency strategy is settled.

## Full Phase Plan (Reference)

### Phase 0: Baseline Inventory and Guardrails
1) Establish a Linux port branch and add CI gating (lint + unit tests only).  
2) Freeze Windows behavior expectations for parity (feature list + golden logs).  
3) Define target distro set (Ubuntu LTS + Fedora latest).  
4) Collect Windows-only dependency map (UIA, COM, WASAPI, etc.).  
5) Create compatibility matrix (feature vs OS/API availability).  

### Phase 1: Platform Abstraction Layer (PAL)
1) Introduce `source/platform/{windows,linux,common}` and runtime factory.  
2) Define interfaces for accessibility, input, audio, clipboard/system, process/focus.  
3) Route core imports through PAL, minimizing direct `win*` imports.  
4) Add Linux stubs with explicit not-supported errors.  

### Phase 2: Accessibility API Backend (AT-SPI2)
1) Implement AT-SPI2 handler analogous to current accessibility handlers.  
2) Map roles/states.  
3) Implement TextInfo for AT-SPI text interfaces.  
4) Implement event dispatch (focus/state/name/description/caret).  
5) Validate object nav/review/browse mode behavior.  
6) Add cache/throttling for D-Bus overhead.  

### Phase 3: Input and Focus Infrastructure
1) Keyboard input (X11 XInput2; Wayland portal/libinput path).  
2) Mouse input (X11 + Wayland path).  
3) Touch gesture translation from Linux input stack.  
4) System/global hotkeys strategy + local-only fallback mode.  

### Phase 4: Audio + Speech Output
1) Replace WASAPI path with PipeWire/Pulse/ALSA fallback strategy.  
2) Implement `nvwave` Linux-capable backend equivalent.  
3) Add Speech Dispatcher synth + keep eSpeak NG direct fallback.  
4) Route tones/beeps through same backend.  

### Phase 5: Braille and HID
1) Prioritize brlapi integration.  
2) Replace COM discovery paths with udev/HID/Bluetooth discovery.  
3) Validate braille key input on X11 and Wayland.  

### Phase 6: Native Helper Replacement (nvdaHelper)
1) Identify DLL injection usage points.  
2) Replace injection-based virtual buffer model with AT-SPI/DOM path.  
3) Remove Windows RPC/COM proxy generation requirements for Linux.  
4) Retain Linux-native helper code only for real performance bottlenecks.  

### Phase 7: GUI and UX Adaptation
1) Audit wxPython compatibility on Linux.  
2) Replace Windows-only GUI hooks with cross-platform equivalents.  
3) Validate settings/add-on store UX on Linux.  
4) Validate tray/status integration with compositor fallbacks.  

### Phase 8: Packaging and Distribution
1) Add Linux build scripts/toolchain support.  
2) Add Flatpak + distro package definitions.  
3) Replace NSIS/AppX flow for Linux packages.  
4) Optional systemd user service for startup.  

### Phase 9: Tests and CI
1) Split OS-agnostic vs Windows-only tests.  
2) Add Linux system tests (AT-SPI nav, speech output, basic UI).  
3) Add Linux CI job (lint + unit + smoke).  
4) Keep Windows CI parity checks unchanged.  

### Phase 10: Documentation and Migration
1) Document Linux build/run in `projectDocs/dev/`.  
2) Document Linux limitations in user guide.  
3) Add migration notes for add-on authors.  
4) Stage beta via feature flags and incremental enablement.  

## Development Notes

### Current Workspace State

- This repo is already a git working tree (`.git` present).
- Linux-port work is committed incrementally on the `linux-port` branch.

### UV / Python Setup Notes

- `uv` is available (`uv 0.9.18`).
- Project `pyproject.toml` is set to:
  - `[tool.uv] python-preference = "managed"`
- Placeholder workspace package files were added to satisfy workspace members:
  - `miscDeps/pyproject.toml`
  - `include/nvda-mathcat/pyproject.toml`
- Local managed interpreter installed:
  - Python `3.13.11` under `.uv-python/`

### UV Command Notes for This Environment

- Use local UV dirs in this repo to avoid restricted global cache/install locations:
  - `UV_CACHE_DIR=$PWD/.uv-cache`
  - `UV_PYTHON_INSTALL_DIR=$PWD/.uv-python`
- Example:
  - `uv run python -V`

### Known Blockers

- Full `uv run pytest ...` currently fails while building `fast-diff-match-patch` due to missing MSVC build tools (`Microsoft Visual C++ 14.0+`).
- Until build tools are available, use targeted validation where possible and keep Linux-port tests dependency-light.

### Implementation Notes

- Replace direct imports of `winAPI`, `winBindings`, `winUser`, `winKernel` with PAL interfaces.
- Map UIA/MSAA/IA2 concepts to AT-SPI2 equivalents:
  - Focus events -> `object:state-changed:focused`
  - Name/description -> `accessible:property-change`
  - Text caret -> `object:text-caret-moved`
- Use D-Bus async event handling (GLib/async strategy) and plan event coalescing early.
