# Phase 1: Platform Abstraction Layer (PAL)

Date: 2026-02-16

## Summary

Phase 1 PAL scaffolding is now in place under `source/platform` and core startup has been further routed through PAL for Windows-specific accessibility lifecycle imports.

## Package structure

- `source/platform/common/*`: shared interfaces and common errors.
- `source/platform/windows/*`: Windows wrappers around existing modules.
- `source/platform/linux/*`: Linux stubs that raise clear "not supported yet" errors.
- `source/platform/pal.py`: runtime platform service factory.

## Interfaces defined

`source/platform/common/interfaces.py` defines adapters for:

- Accessibility adapters (object/event lifecycle + UIA/IAccessible/legacy-console hooks).
- Input hooks (keyboard/mouse/touch initialize/terminate).
- Audio output and tones (`play_wave_file`, `beep`).
- Clipboard integration (`get_text`, `set_text`).
- System info and power/battery (`get_os_version_string`, `register_application_restart`, `get_battery_status`).
- Process/window enumeration and focus tracking (`get_desktop_window`, `get_foreground_window`, `list_window_handles`, `list_process_ids`).
- Supporting adapters (windowing, message window, display, session).

## Core routing updates

`source/core.py` now routes these through PAL:

- Legacy console accessibility initialization/termination.
- UIA initialization/termination.
- IAccessible initialization/termination.

This removes direct `winConsoleHandler` imports from core and keeps Windows-specific wiring behind PAL adapters.

## Linux stubs

Linux adapters continue to raise:

- `NotSupportedYetError("<capability>")`

with explicit capability names, including new Phase 1 methods (battery status, process/window enumeration, accessibility lifecycle hooks, tone playback).
