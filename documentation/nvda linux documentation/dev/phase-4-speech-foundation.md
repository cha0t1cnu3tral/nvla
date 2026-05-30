# Phase 4: Linux Speech Foundation

Date: 2026-05-30

## Summary

The first Linux-native speech path is in place for an early `0.1` milestone. It intentionally avoids the Windows-oriented `nvwave` and WASAPI stack while the full PipeWire/Pulse/ALSA audio backend is still pending.

## Implemented

- Added `source/platform/linux/speech.py`.
  - Prefers `spd-say`, the Speech Dispatcher command-line client.
  - Falls back to the `espeak-ng` command when Speech Dispatcher is unavailable.
  - Supports asynchronous speech requests, process cleanup, and cancellation.
  - Uses `spd-say --wait` so completion can be observed and `spd-say --cancel` to clear queued Speech Dispatcher output.
- Added `source/synthDrivers/linuxSpeech.py`.
  - Exposes the Linux transport through NVDA synth-driver discovery.
  - Sends text sequences to the selected Linux transport.
  - Reports the last speech index and completion notification after output finishes.
  - Cancels stale speech when a newer announcement replaces it.
- Updated automatic synth selection.
  - Linux tries `linuxSpeech` and then `silence`.
  - Windows keeps its existing `oneCore`, `espeak`, and `silence` order.
- Removed early Linux boot dependencies on Windows-only helper/audio initialization.
  - Linux skips `NVDAHelper`, `nvwave`, tones, sound splitting, audio ducking, and comtypes logging.
  - Unfinished Linux mouse and touch hooks are treated as explicit non-fatal limitations during startup.
  - Linux DPI setup and session pumping use non-fatal compositor/toolkit fallbacks.
  - Linux uses a lifecycle-compatible placeholder instead of a Win32 message window.

## Validation

Run:

```powershell
uv run python tests/linuxPortUnitRunner.py
```

The dependency-light suite validates Speech Dispatcher selection, eSpeak NG fallback, cancellation, process cleanup, synth-driver completion notifications, stale-notification suppression, and platform-specific availability.

## Scope

This is an early speech path, not the final Linux audio architecture. It is enough to connect NVDA announcements to system speech tools during `0.1` bring-up.

Remaining Phase 4 work:

- Replace command-per-announcement execution with a persistent Speech Dispatcher client.
- Support rate, pitch, volume, language, and voice settings.
- Add a PipeWire/Pulse/ALSA-backed `nvwave` equivalent for wave files and tones.
- Validate speech latency and cancellation on real Linux desktops.

## Minimal Linux `0.1` Checklist

The first usable screen-reader preview still needs:

- Real X11 keyboard capture with pass-through enforcement.
- A documented restricted Wayland fallback until compositor-specific global capture is available.
- Continue Linux startup cleanup for remaining Windows-only imports beyond the early helper/audio path.
- Real desktop smoke tests: focus an application, receive AT-SPI focus events, speak the focused control, and execute commands such as `NVDA+t`.
- A simple launch script and package dependency list for Speech Dispatcher, eSpeak NG, AT-SPI2, Python, and wxPython.
