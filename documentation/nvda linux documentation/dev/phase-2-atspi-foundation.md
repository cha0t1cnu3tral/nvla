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
  - Linux adapter now exposes translated AT-SPI event listener registration for higher layers.
  - Windows-specific compatibility hooks (`UIA`, legacy console) are explicit no-ops on Linux.
- Added unit tests:
  - `tests/unit/test_linuxAtspiMappings.py`.
  - `tests/unit/test_linuxAtspiEventTranslation.py`.

## Newly completed in this slice

- Raw AT-SPI events are normalized into `TranslatedATSPIEvent` payloads.
- Repeated focus, property, and caret updates for the same source are coalesced before dispatch.
- Pumping the Linux accessibility adapter now flushes translated events to registered listeners, giving the next object-wrapper stage a stable handoff point.
- Linux accessibility now creates stable placeholder NVDA objects per translated AT-SPI source and routes focus/name/description/value/caret updates into NVDA's event queue.
- Backend translated-event buffering is now bounded to prevent unbounded growth under bursty D-Bus traffic.
- Queue eviction now prefers dropping non-focus events first, preserving focus continuity under load.
- Linux AT-SPI object caching now uses bounded eviction and is explicitly cleared on adapter termination.

## Remaining Phase 2 work

- AT-SPI TextInfo implementation and integration with NVDA text navigation.
- Full event dispatch bridge from translated Linux events into real NVDA objects and the NVDA event queue.
- Object tree navigation and browse/review parity validation.
- D-Bus event prioritization and smarter throttling (beyond key-based coalescing and bounded buffering).
