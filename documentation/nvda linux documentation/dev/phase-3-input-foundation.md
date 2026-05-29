# Phase 3: Input Foundation

Date: 2026-05-29

## Summary

Initial Linux input scaffolding is in place, focused on a stable, testable keyboard event model before committing to X11 or Wayland capture backends.

## Implemented

- Updated `source/platform/linux/input.py`:
  - Added `LinuxKeyEvent`, a normalized keyboard event payload.
  - Added raw-key translation for common backend event shapes.
  - Normalizes key names and modifier names.
  - Adds a deterministic `gestureName` representation such as `control+shift+A`.
  - Allows dependency-light event injection through `feedRawKeyboardEvent`.
  - Allows listeners and an observer to receive normalized key events.
  - Makes keyboard initialize/terminate non-fatal while real global hooks are still pending.
  - Added `LinuxKeyboardGesture`, a gesture-shaped wrapper that exposes the same user-facing `kb(desktop):...`, `kb(laptop):...`, and `kb:...` identifiers used by existing NVDA keyboard gesture bindings.
  - Avoids a separate Linux gesture namespace so Windows NVDA gestures can be reused on Linux wherever the physical/user-facing keystroke is the same.
  - Made `LinuxKeyboardGesture` compatible with NVDA's `inputCore.InputGesture` contract when `inputCore` is available.
  - Added an `executeKeyboardGesture` handoff helper and `LinuxInputAdapter.enableInputCoreGestureExecution()` so injected Linux key events can be executed through an `inputCore`-style manager.
  - Registers the Linux keyboard gesture class as the `kb` gesture source when execution is enabled, preserving display lookup compatibility for `kb(...)` gesture identifiers.
  - Wired Linux startup through `core.main()` so the Linux input adapter hands key-down gestures to `inputCore.manager` after `inputCore.initialize()`.
  - Added key-down-only gesture executor dispatch for the `inputCore` handoff.
- Added `tests/unit/test_linuxInput.py`.
- Added Linux input tests to `tests/linuxPortUnitRunner.py`.

## Validation

Run focused Linux-port validation from the repository root with:

```powershell
uv run python tests/linuxPortUnitRunner.py
```

This currently validates AT-SPI accessibility scaffolding plus Linux keyboard event normalization, Windows-compatible gesture identifiers, and an injected `inputCore`-style execution handoff without requiring a Linux desktop session.

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

Remaining:

- X11 backend capture, likely XInput2.
- Wayland-compatible strategy, likely portal/compositor-specific support plus a restricted fallback mode.
- NVDA modifier handling on Linux.
- Secure handling of global hotkeys and pass-through behavior.
- Integration tests on a real Linux desktop.
