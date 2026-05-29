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
- Linux AT-SPI objects now expose a concrete `TextInfo` implementation for story/caret/selection operations, backed by the AT-SPI text interface when available and by translated caret fallback state otherwise.
- Added Linux TextInfo unit coverage in `tests/unit/test_linuxAtspiEventTranslation.py` for:
  - Story and caret retrieval from an AT-SPI text interface.
  - Caret and selection updates propagated back through AT-SPI text primitives.
  - Caret-position fallback from translated `object:text-caret-moved` events when AT-SPI text is not available.
- Fixed Linux AT-SPI object cache initialization so the first translated event is immediately applied to new objects (for example initial property-change payloads and initial caret offsets).
- Linux event bridge now falls back to generic `stateChange` dispatch for unsuffixed or unmapped AT-SPI property-change events.
- Added normalized AT-SPI source translation so Linux NVDA objects can be created from raw accessibles as well as from queued events.
- Linux accessibility now exposes `getNVDAObjectFromAccessible` for early object-creation integration points that already have an AT-SPI accessible.
- Unsuffixed `accessible:property-change` events now read the property name from `detail1` when available.
- Focus-event buffering now keeps only the latest focus event globally, while property and caret queues remain keyed per source.
- Added `tests/linuxPortUnitRunner.py` so dependency-light Linux AT-SPI unit tests can run from a Windows checkout before `nvdaHelperLocal.dll` is available.
- Linux AT-SPI placeholder objects now expose basic object navigation getters for parent, first/last child, and previous/next sibling using AT-SPI-style accessible relationships.
- Navigation-created Linux AT-SPI objects flow through the same bridge cache and role/state mapping path as event-created objects.
- Linux AT-SPI placeholder objects now expose screen geometry from component extents when available, with fallback to accessible-provided extents and invalid-geometry filtering.
- Linux AT-SPI TextInfo now exposes offset-to-screen bounds through AT-SPI text character/range extents.
- Linux AT-SPI TextInfo now supports screen-point hit testing through AT-SPI text `getOffsetAtPoint`.
- Linux AT-SPI TextInfo now supports line and word offset expansion, preferring AT-SPI-style `getTextAtOffset` boundaries and falling back to local story-text parsing.
- Linux AT-SPI TextInfo now supports sentence and paragraph expansion using the same AT-SPI-boundary-first, local-fallback strategy.

## Validation

Run focused Linux-port validation from the repository root with:

```powershell
uv run python tests/linuxPortUnitRunner.py
```

This currently covers AT-SPI role/state mapping, event translation, queue coalescing, object caching, event routing, basic object navigation, object geometry, TextInfo line/word/sentence/paragraph expansion, TextInfo geometry/hit-testing, and baseline Linux TextInfo behavior.

## Remaining Phase 2 work

- Replace placeholder Linux AT-SPI objects with deeper integration into the existing NVDA object creation flow.
- Expand object tree navigation coverage beyond parent/child/sibling primitives and validate browse/review parity.
- D-Bus event prioritization and smarter throttling (beyond key-based coalescing and bounded buffering).
- Extend AT-SPI TextInfo beyond baseline primitives with richer formatting and embedded-object handling.
