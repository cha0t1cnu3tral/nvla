# Phase 3: Input Foundation

Date: 2026-05-29

## Summary

Initial Linux input scaffolding, X11 global keyboard observation, and X11
NVDA-modifier command suppression are in place. Wayland global capture and
full pass-through parity remain pending.

## Implemented

- Updated `source/platform/linux/input.py`:
  - Added `LinuxKeyEvent`, a normalized keyboard event payload.
  - Added raw-key translation for common backend event shapes.
  - Normalizes key names and modifier names.
  - Adds a deterministic `gestureName` representation such as `control+shift+A`.
  - Allows dependency-light event injection through `feedRawKeyboardEvent`.
  - Allows listeners and an observer to receive normalized key events.
  - Makes keyboard initialize/terminate non-fatal when a global source is unavailable.
  - Added `LinuxKeyboardGesture`, a gesture-shaped wrapper that exposes the same user-facing `kb(desktop):...`, `kb(laptop):...`, and `kb:...` identifiers used by existing NVDA keyboard gesture bindings.
  - Avoids a separate Linux gesture namespace so Windows NVDA gestures can be reused on Linux wherever the physical/user-facing keystroke is the same.
  - Made `LinuxKeyboardGesture` compatible with NVDA's `inputCore.InputGesture` contract when `inputCore` is available.
  - Added an `executeKeyboardGesture` handoff helper and `LinuxInputAdapter.enableInputCoreGestureExecution()` so injected Linux key events can be executed through an `inputCore`-style manager.
  - Registers the Linux keyboard gesture class as the `kb` gesture source when execution is enabled, preserving display lookup compatibility for `kb(...)` gesture identifiers.
  - Wired Linux startup through `core.main()` so the Linux input adapter hands key-down gestures to `inputCore.manager` after `inputCore.initialize()`.
  - Added key-down-only gesture executor dispatch for the `inputCore` handoff.
  - Added a keyboard event-source boundary for physical capture backends.
  - Added a manual event source for dependency-light tests and early smoke tools.
  - Added session-based X11 and Wayland event-source selection.
  - Added X11 RECORD observation through `python-xlib`, including global
    key-down/key-up delivery, modifier tracking, a background capture thread,
    and clean context shutdown.
  - Added X11 synchronous passive grabs for configured NVDA modifier keys,
    including handled-command suppression and unhandled-event replay.
  - Keeps the Wayland source as an explicit local-only fallback until a
    compositor-compatible strategy is implemented.
  - Added Linux NVDA modifier normalization for configured Caps Lock, numpad Insert, and extended Insert keys so they produce the same `NVDA+...` gesture names as Windows.
  - Maps Linux Super key names to NVDA's existing `windows` modifier identifier so commands using that modifier remain compatible with the shared gesture maps.
  - Maps common Linux navigation and keypad names such as `Page_Up`, `Left`, and `KP_Enter` to the existing NVDA key identifiers such as `pageUp`, `leftArrow`, and `numpadEnter`.
  - Tracks configured NVDA modifier key-down/key-up state so physical event sources do not need to repeat modifier metadata on each raw event.
  - Keeps modifier-only key events observable without executing them as `inputCore` commands.
  - Marks a configured NVDA modifier for normal pass-through when it is pressed twice within the configured multi-press timeout, matching the existing Windows interaction.
  - Marks key events for desktop pass-through when `inputCore` reports that no NVDA command handled the gesture.
  - Dispatches normalized observer/listener events after the NVDA command handoff so physical backends and diagnostics see the final pass-through decision.
  - Exposes keyboard capture mode as disabled, global, global-commands,
    global-observe-only, or local-only so callers can distinguish complete
    enforcement, X11 command grabs, RECORD observation, and restricted fallback.
  - Makes keyboard capture lifecycle idempotent and falls back to local-only mode when a physical backend fails during startup.
  - Keeps repeats and the matching key-up marked for pass-through after an unbound key-down, preserving complete desktop key sequences for physical backends.
- Added `tests/unit/test_linuxInput.py`.
- Added Linux input tests to `tests/linuxPortUnitRunner.py`.

## Validation

Run focused Linux-port validation from the repository root with:

```powershell
uv run python tests/linuxPortUnitRunner.py
```

This currently validates AT-SPI accessibility scaffolding plus Linux keyboard event normalization, Windows-compatible gesture identifiers, and an injected `inputCore`-style execution handoff without requiring a Linux desktop session.
The Linux input tests also extract every built-in `kb:` binding from `source/globalCommands.py` and verify that the Linux translator emits an equivalent normalized identifier.

## Keyboard Support Status

This is not full keyboard support yet. It is the middle layer that real keyboard backends will feed.

Done:

- Stable normalized key event type.
- Modifier/key normalization.
- Listener/observer dispatch path.
- Linux keyboard gesture identifiers and display names.
- Desktop, laptop, and all-layout NVDA keyboard binding compatibility without a special Linux binding mode.
- `inputCore`-compatible gesture object shape.
- Injected key-down execution through an `inputCore`-style manager.
- Linux startup wiring that enables keyboard execution through `inputCore.manager`.
- Key-down-only gesture executor callback.
- Windows-testable injected event path.
- Keyboard event-source interface for X11/Wayland capture backends.
- Manual event source for Windows-hosted tests.
- X11 RECORD global observation with dependency-light fake-X11 tests.
- X11 NVDA-modifier command grabs with handled suppression and unhandled replay.
- NVDA modifier key normalization for Linux key names.
- Windows-compatible Super, navigation, and keypad key-name aliases.
- Held NVDA modifier tracking across physical key-down/key-up events.
- Modifier-only events are filtered from the `inputCore` execution handoff.
- NVDA modifier double-press pass-through intent is exposed to physical event sources.
- Unbound gesture pass-through intent is exposed to physical event sources.
- Restricted local-only fallback mode is explicit when no global keyboard source can start.
- X11 RECORD observation mode remains explicit for diagnostics.
- X11 command-grab mode is explicit because desktop pass-through parity still
  needs validation.

Remaining:

- Validate X11 command suppression and pass-through replay against real
  applications, then deepen the backend where parity gaps remain.
- Wayland-compatible implementation strategy, likely portal/compositor-specific support on top of the explicit restricted fallback mode.
- Full NVDA modifier behavior on Linux, including system Sticky Keys latch/lock support and physical backend pass-through enforcement.
- Secure handling of global hotkeys and pass-through behavior.
- Integration tests on a real Linux desktop.
