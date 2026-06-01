# Phase 0: Compatibility Matrix (Feature vs OS/API)

Date: 2026-06-01

Legend:

- `Available`: existing stable path in current platform.
- `Initial path available`: committed preview path that still needs deeper
  integration or desktop validation.
- `Planned`: target path selected, implementation pending.
- `Gap`: no committed implementation path yet.

| Feature area | Windows (current) | Linux target | Status |
| --- | --- | --- | --- |
| Accessibility tree and events | UIA + IAccessible + IA2/COM | AT-SPI2 over D-Bus | Initial path available |
| Text ranges / review | UIA TextPattern + IAccessible text variants | AT-SPI text interfaces | Initial path available |
| Global keyboard hooks | Win32 hooks / `SendInput` ecosystem | X11 capture + restricted Wayland fallback | Initial path available |
| Mouse tracking / routing | Win32 cursor APIs | X11 RECORD observation + AT-SPI hit testing | Initial path available |
| Touch gestures | Windows touch and gesture stack | Wayland/libinput gesture translation | Gap |
| Speech output | SAPI, eSpeak, Windows audio routing | Speech Dispatcher + eSpeak NG command fallback | Initial path available |
| Audio backend | WASAPI-centric behavior | PipeWire primary, Pulse fallback, ALSA last resort | Planned |
| Tones/beeps | Existing `tones.py`/`nvwave` path | Command-backed preview output, streaming backend later | Initial path available |
| Braille transport and I/O | COM ports, HID, Windows device discovery | brlapi + udev/HID/Bluetooth discovery | Planned |
| Virtual buffers | `nvdaHelper` injection backends | AT-SPI-based virtual buffer model | Gap |
| Config/system integration | Registry + Windows shell integration | File-based config + preview desktop/service artifacts | Initial path available |
| Tray/status integration | Windows system tray APIs | StatusNotifier/AppIndicator + fallback UI | Planned |
| Installer/packaging | NSIS/AppX tooling | User-level preview installer; Flatpak and distro packages later | Initial path available |
| CI parity checks | Mature Windows CI pipeline | Linux-port Windows/Ubuntu focused gate + packaging smoke | Available (branch gate) |

## Priority for closing critical gaps

1. AT-SPI2 object/event backend
2. Input/focus infrastructure for X11 and Wayland
3. Audio/speech stack replacement for non-Windows hosts
4. Braille discovery and transport on Linux
