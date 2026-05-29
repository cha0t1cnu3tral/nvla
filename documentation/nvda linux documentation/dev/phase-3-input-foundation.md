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
- Added `tests/unit/test_linuxInput.py`.
- Added Linux input tests to `tests/linuxPortUnitRunner.py`.

## Validation

Run focused Linux-port validation from the repository root with:

```powershell
uv run python tests/linuxPortUnitRunner.py
```

This currently validates AT-SPI accessibility scaffolding plus Linux keyboard event normalization and dispatch without requiring a Linux desktop session.

## Keyboard Support Status

This is not full keyboard support yet. It is the middle layer that real keyboard backends will feed.

Done:

- Stable normalized key event type.
- Modifier/key normalization.
- Listener/observer dispatch path.
- Windows-testable injected event path.

Remaining:

- X11 backend capture, likely XInput2.
- Wayland-compatible strategy, likely portal/compositor-specific support plus a restricted fallback mode.
- Conversion from `LinuxKeyEvent` into NVDA `InputGesture`/gesture-map execution.
- NVDA modifier handling on Linux.
- Secure handling of global hotkeys and pass-through behavior.
- Integration tests on a real Linux desktop.

