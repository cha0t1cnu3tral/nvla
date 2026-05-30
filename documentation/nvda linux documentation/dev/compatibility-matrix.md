# Phase 0: Compatibility Matrix (Feature vs OS/API)

Date: 2026-02-16

Legend:

- `Available`: existing stable path in current platform.
- `Planned`: target path selected, implementation pending.
- `Gap`: no committed implementation path yet.

| Feature area | Windows (current) | Linux target | Status |
| --- | --- | --- | --- |
| Accessibility tree and events | UIA + IAccessible + IA2/COM | AT-SPI2 over D-Bus | Planned |
| Text ranges / review | UIA TextPattern + IAccessible text variants | AT-SPI text interfaces | Planned |
| Global keyboard hooks | Win32 hooks / `SendInput` ecosystem | X11 XInput2 + Wayland/libinput or portals | Planned |
| Mouse tracking / routing | Win32 cursor APIs | X11 input + Wayland compositors/portals | Planned |
| Touch gestures | Windows touch and gesture stack | Wayland/libinput gesture translation | Gap |
| Speech output | SAPI, eSpeak, Windows audio routing | Speech Dispatcher + eSpeak NG command fallback | Initial path available |
| Audio backend | WASAPI-centric behavior | PipeWire primary, Pulse fallback, ALSA last resort | Planned |
| Tones/beeps | Existing `tones.py`/`nvwave` path | Linux audio backend equivalent | Planned |
| Braille transport and I/O | COM ports, HID, Windows device discovery | brlapi + udev/HID/Bluetooth discovery | Planned |
| Virtual buffers | `nvdaHelper` injection backends | AT-SPI-based virtual buffer model | Gap |
| Config/system integration | Registry + Windows shell integration | File-based config + desktop/session integrations | Planned |
| Tray/status integration | Windows system tray APIs | StatusNotifier/AppIndicator + fallback UI | Planned |
| Installer/packaging | NSIS/AppX tooling | Flatpak primary, distro packages secondary | Planned |
| CI parity checks | Mature Windows CI pipeline | Linux-port branch gate (lint + unit) | Available (branch gate) |

## Priority for closing critical gaps

1. AT-SPI2 object/event backend
2. Input/focus infrastructure for X11 and Wayland
3. Audio/speech stack replacement for non-Windows hosts
4. Braille discovery and transport on Linux
