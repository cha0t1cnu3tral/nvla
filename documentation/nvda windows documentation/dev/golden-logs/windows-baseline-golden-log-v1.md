# Windows Baseline Golden Log v1

Captured date: 2026-02-16  
Purpose: initial parity baseline for Linux rewrite work.

## Required trace checkpoints

| Checkpoint | Expected signal |
| --- | --- |
| Startup | Core initialization completes without fatal errors. |
| Focus event | Foreground focus changes are emitted and announced. |
| Text navigation | Character/word/line reading commands produce matching output patterns. |
| Browse mode interaction | Element navigation commands emit expected role/name transitions. |
| Speech interruption | New speech interrupts previous output with no deadlock. |
| Shutdown | Termination path completes and cleans up modules/resources. |

## Notes

- This v1 file captures required checkpoints and expected patterns.
- Concrete machine traces can be attached in later revisions as appendices.
