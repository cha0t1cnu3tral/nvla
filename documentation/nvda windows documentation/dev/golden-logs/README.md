# Golden Logs

These logs define expected Windows behavior signatures used to detect regressions during Linux porting.

## How to use

- Capture equivalent startup, focus, speech, and shutdown traces on a known-good Windows build.
- Compare Linux-port traces against this baseline at the behavior level.
- Record deltas with a short rationale when behavior intentionally diverges.

## Versioning

- Keep immutable snapshots named `windows-baseline-golden-log-vN.md`.
- Add new files for updates rather than rewriting historical baselines.
