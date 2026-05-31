# NVDA Linux Port Status

Last updated: 2026-05-30

## Current phase

Phase 0 and Phase 1 are established. Phase 2 AT-SPI accessibility foundations are usable for dependency-light testing, and Phase 3 keyboard input work has started:

- Branch and CI quality gate established for Linux-port work.
- Windows behavior parity baseline and golden-log checkpoints defined.
- Initial distro targets selected (Ubuntu LTS and Fedora latest).
- Windows-only dependency map and compatibility matrix drafted.
- PAL structure added with Windows wrappers and Linux stubs.
- Core accessibility lifecycle imports are now routed through PAL.
- AT-SPI events are translated, coalesced, and routed into placeholder Linux NVDA objects.
- Linux AT-SPI objects expose basic tree navigation, screen geometry, and baseline TextInfo review primitives.
- Linux keyboard events can be normalized and handed to existing `kb:` gesture bindings through `inputCore`.
- Linux NVDA modifier handling covers configured modifier keys, held modifiers, and pass-through intent.
- Linux Super, navigation, and keypad key names are translated to the existing NVDA identifiers so built-in Windows keyboard command maps can be reused.
- Keyboard startup exposes an explicit local-only fallback while real X11 and Wayland capture backends remain pending.
- Initial Linux speech output is available through Speech Dispatcher, with an `espeak-ng` command fallback.
- Linux automatic synth selection now prefers the Linux-native speech path without changing Windows synth selection.
- Linux document navigation primitives cover line movement and quick navigation for headings, links, form fields, lists, tables, and landmarks.
- Early Linux startup skips Windows-only helper/audio initialization so speech bring-up is no longer tied to `NVDAHelper`, WASAPI, tones, or sound splitting.
- The early `0.1` Linux path also skips optional Windows-heavy braille, vision, display-model, remote, update, and hardware-detection subsystems until Linux implementations are added.
- A user-level Linux preview launcher, desktop entry, and optional systemd service are available under `packaging/linux/`.

## What to expect right now

- Linux support is not yet production-ready.
- The current focus is physical keyboard capture, Linux boot-path cleanup, and real desktop AT-SPI-to-speech smoke testing.
- Global X11 and Wayland keyboard capture are not implemented yet.
- User-facing Linux builds will come after core accessibility, input, audio, and packaging work.
