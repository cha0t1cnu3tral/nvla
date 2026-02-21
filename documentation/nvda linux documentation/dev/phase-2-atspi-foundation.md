# Phase 2: AT-SPI2 Foundation

Date: 2026-02-19

## Summary

Initial AT-SPI2 backend scaffolding is now in place in the Linux PAL accessibility adapter.

## Implemented

- Added `source/platform/linux/atspi_backend.py`:
  - AT-SPI2 binding bootstrap via `pyatspi`.
  - Event listener lifecycle for:
    - `object:state-changed:focused`
    - `accessible:property-change`
    - `object:text-caret-moved`
  - GLib main-context pumping support in `pump_all`.
- Added `source/platform/linux/atspi_mappings.py`:
  - Role mapping from AT-SPI role constants to `controlTypes.Role`.
  - State mapping from AT-SPI state constants to `controlTypes.State`.
  - Visibility/offscreen inversion support for `STATE_VISIBLE` and `STATE_SHOWING`.
- Updated `source/platform/linux/accessibility.py`:
  - Linux adapter now uses AT-SPI2 backend lifecycle for initialize/pump/terminate.
  - Windows-specific compatibility hooks (`UIA`, legacy console) are explicit no-ops on Linux.
- Added unit tests:
  - `tests/unit/test_linuxAtspiMappings.py`.

## Remaining Phase 2 work

- AT-SPI TextInfo implementation and integration with NVDA text navigation.
- Full event dispatch bridge from AT-SPI events to NVDA event queue.
- Object tree navigation and browse/review parity validation.
- Event coalescing/cache strategy for D-Bus traffic control.
