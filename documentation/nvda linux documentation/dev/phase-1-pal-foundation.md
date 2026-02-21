# Phase 1: Platform Abstraction Layer (PAL) Foundation

Date: 2026-02-16

## What was added

- New PAL package at `source/platform/` with:
  - `source/platform/windows/*` adapters (wrapping current Windows behavior)
  - `source/platform/linux/*` adapters (clear "not supported yet" stubs)
  - `source/platform/common/*` shared interfaces and errors
  - `source/platform/pal.py` runtime platform service loader

## Interfaces defined

Shared PAL interfaces are in `source/platform/common/interfaces.py`:

- Accessibility adapter (object/event pump lifecycle contract)
- Input adapter (keyboard/mouse/touch hooks)
- Audio adapter (output and wave playback contract)
- Clipboard adapter
- System adapter (OS info + restart registration)
- Process/focus adapter (desktop window primitive)
- Windowing adapter (show mode constants)
- Message window adapter
- Display adapter (DPI awareness)
- Session adapter (initialize/pump)

## Core routing changes

`source/core.py` now routes Windows-specific integration through PAL in key places:

- Message-window pre-handler compatibility accessor
- Restart show mode constant
- Desktop window discovery for object-cache bootstrap
- AppX restart registration
- DPI awareness setup
- OS version logging
- Message-window creation
- Session tracking initialize/pump
- Keyboard/mouse/touch initialization
- Accessibility event pumping

## Linux stubs

Linux PAL modules currently raise `NotSupportedYetError` with explicit capability names, so missing features fail fast and clearly during early bring-up.

## Notes

- This is scaffolding for Phase 1; handlers/modules are not fully migrated yet.
- Additional refactors are needed to move broader core and subsystem imports behind PAL.
