# Phase 0: Target Distro Set

Date: 2026-02-16

## Primary targets

| Distro | Release track | Why included |
| --- | --- | --- |
| Ubuntu LTS | Long-term support | Large user base, stable packages, common enterprise baseline. |
| Fedora (latest stable) | Fast-moving | Good coverage of newer Wayland, PipeWire, and toolchain behavior. |

## Display server coverage

- Wayland: primary target path.
- X11: required compatibility path.

## Packaging priority

1. Flatpak (primary)
2. .deb and .rpm (secondary)
3. AppImage (optional)

## Runtime dependencies to validate on both targets

- AT-SPI2 and D-Bus integration
- Speech Dispatcher and eSpeak NG
- brlapi/brltty
- PipeWire with PulseAudio compatibility
