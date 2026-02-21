# Windows Parity Feature Baseline (Frozen)

Date frozen: 2026-02-16  
Scope: baseline behavior used as parity target while implementing Linux support.

## Core feature baseline

The following areas are frozen as parity-critical unless explicitly re-scoped:

| Area | Baseline expectation |
| --- | --- |
| Startup and shutdown | NVDA starts, initializes drivers/services, and exits cleanly. |
| Focus tracking | Focus changes are announced with role/name/value context. |
| Object navigation | Parent/child/sibling navigation remains stable and predictable. |
| Review cursor | Character/word/line review and copy behavior remain consistent. |
| Speech | Primary synth output, interruption, and queueing behavior are stable. |
| Audio cues | WAV cues and tones play in expected interaction points. |
| Braille | Display output and key input routing remain stable for supported devices. |
| Browse mode | Quick nav keys, element list, and reading commands remain functional. |
| Global commands | Major keyboard commands behave consistently across sessions. |
| Configuration | Profiles, settings persistence, and command line options remain stable. |

## Feature freeze policy

- New Linux work must document whether it preserves, defers, or replaces each baseline behavior.
- Any intentional behavior change must include a rationale and user-facing impact note.
- Regressions against this baseline block parity completion for the affected feature.

## Golden logs

Golden logs for this frozen baseline are tracked in:

- `documentation/nvda windows documentation/dev/golden-logs/README.md`
- `documentation/nvda windows documentation/dev/golden-logs/windows-baseline-golden-log-v1.md`
