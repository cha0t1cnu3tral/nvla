# Phase 0: Windows-Only Dependency Map

Date: 2026-02-16

This map identifies major Windows-bound components that require abstraction or replacement for Linux.

## Accessibility stack

| Component | Current implementation signal | Example references |
| --- | --- | --- |
| MSAA/IAccessible eventing | WinEvent hooks and IAccessible handler | `source/IAccessibleHandler/internalWinEventHandler.py` |
| UI Automation (UIA) | `UIAHandler` usage and UIA COM types | `source/UIAHandler.py`, `source/appModules/calculator.py` |
| COM interface marshaling | COM proxy registration and generated interfaces | `nvdaHelper/remote/COMProxyRegistration.cpp`, `source/comInterfaces_sconscript` |

## Native integration and OS APIs

| Component | Current implementation signal | Example references |
| --- | --- | --- |
| Win32 user/kernel APIs | Direct `winUser`, `winKernel`, `winBindings.*` imports | `source/api.py`, `source/core.py`, `source/eventHandler.py` |
| Windows registry | `winreg` configuration and setup integration | `source/config/__init__.py`, `source/easeOfAccess.py` |
| Session/secure desktop behavior | Windows session tracking and secure desktop helpers | `source/winAPI/sessionTracking.py`, `source/winAPI/secureDesktop.py` |

## Audio stack

| Component | Current implementation signal | Example references |
| --- | --- | --- |
| WASAPI-oriented behavior | Config flags and docs tied to WASAPI | `source/config/configSpec.py` (`useWASAPIForSAPI4`), user docs references |
| Windows audio ducking/session control | `oleacc` utility state and pycaw COM usage | `source/audioDucking.py`, `source/audio/soundSplit.py` |
| Windows wave path in runtime | `nvwave` startup/termination wiring | `source/core.py`, `source/browseMode.py` |

## Input and device access

| Component | Current implementation signal | Example references |
| --- | --- | --- |
| Global keyboard/mouse with Win32 | `SendInput`, `getCursorPos`, Win event semantics | `source/brailleInput.py`, `source/globalCommands.py` |
| Device enumeration via SetupAPI/registry | Serial/HID/BT discovery under Windows APIs | `source/hwPortUtils.py`, `source/bdDetect.py` |
| COM-port-centric braille paths | Driver comments and COM port assumptions | `source/brailleDisplayDrivers/alva.py`, `source/bdDetect.py` |

## Helper binaries / injection

| Component | Current implementation signal | Example references |
| --- | --- | --- |
| `nvdaHelper` Windows DLL and injection model | VBuf backends and remote helper code | `nvdaHelper/vbufBackends/*`, `nvdaHelper/remote/*` |
| UIA remote helper dependency | UIA remote build scripts and linked libs | `nvdaHelper/UIARemote/sconscript` |

## Porting implications

- Introduce a platform abstraction layer so core modules stop importing `win*` APIs directly.
- Replace COM/UIA/MSAA paths with AT-SPI2 equivalents on Linux.
- Replace Windows audio/input/device plumbing with PipeWire/Pulse/libinput/udev paths.
- Rework `nvdaHelper` responsibilities to Linux-native helpers only where needed.
