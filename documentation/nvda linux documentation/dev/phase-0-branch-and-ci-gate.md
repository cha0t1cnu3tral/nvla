# Phase 0: Branch and CI Gate

Date: 2026-02-16

## Branch

- Local branch created: `linux-port`.
- Purpose: isolate Linux port planning and early scaffolding from `master`.

## CI gate (lint + unit tests only)

A dedicated workflow was added:

- `.github/workflows/linuxPortGate.yml`

Gate behavior:

- Triggers on push/PR for `linux-port` and `linux-port/**`.
- Runs two jobs only:
  - `lint` via `runlint.bat`
  - `unitTests` via `rununittests.bat -v`
- Uploads `testOutput/unit/unitTests.xml` as an artifact.

This keeps early branch quality checks fast and focused while deeper Linux system testing is still being built.
