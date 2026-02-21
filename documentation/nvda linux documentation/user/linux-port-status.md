# NVDA Linux Port Status

Last updated: 2026-02-16

## Current phase

Phase 0 is established and Phase 1 PAL scaffolding has started:

- Branch and CI quality gate established for Linux-port work.
- Windows behavior parity baseline and golden-log checkpoints defined.
- Initial distro targets selected (Ubuntu LTS and Fedora latest).
- Windows-only dependency map and compatibility matrix drafted.
- PAL structure added with Windows wrappers and Linux stubs.
- Core accessibility lifecycle imports are now routed through PAL.

## What to expect right now

- Linux support is not yet production-ready.
- The current focus is architecture and parity planning, not full feature availability.
- User-facing Linux builds will come after platform abstractions and AT-SPI2 backend work.
