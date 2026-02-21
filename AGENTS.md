# NVDA Linux Port Plan (Working)

This file tracks Linux port progress in this checkout, what is next, and practical development notes.

## Assumptions and Target Constraints

- Primary target: modern Linux desktops with Wayland and X11 support.
- Accessibility API target: AT-SPI2 (ATK/AT-SPI over D-Bus).
- GUI toolkit: keep wxPython where feasible, with Linux-specific integration updates.
- Speech output: eSpeak NG and Speech Dispatcher first.
- Braille output: brltty/brlapi first.
- Packaging target: Flatpak primary, .deb/.rpm secondary.

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

## Next Phase Work (Immediate)

### Phase 2: Accessibility API Backend (AT-SPI2)

1. Implement event bridge in `ATSPI2Backend._onAtspiEvent`:
   - Focus (`object:state-changed:focused`)
   - Property changes (`accessible:property-change`)
   - Caret (`object:text-caret-moved`)
2. Add AT-SPI object wrapper + role/state mapping integration into NVDA object creation flow.
3. Implement AT-SPI TextInfo primitives for review/navigation.
4. Add event coalescing and cache policy to reduce D-Bus overhead.
5. Add Linux-focused unit tests for mapping/event translation behavior.

### Phase 3 Prep (After Phase 2 Bridge Is Usable)

1. Define X11/Wayland input adapter interface details in PAL.
2. Implement initial keyboard focus path for Linux session.
3. Add fallback mode when global hooks are unavailable.

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
- Linux-port work currently appears as local/uncommitted changes in this checkout.

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
