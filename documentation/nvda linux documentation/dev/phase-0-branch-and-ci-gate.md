# Phase 0: Branch and CI Gate

Date: 2026-02-16

## Branch

- Local branch created: `linux-port`.
- Purpose: isolate Linux port planning and early scaffolding from `master`.

## CI gate (focused Linux-port tests)

A dedicated workflow was added:

- `.github/workflows/linuxPortGate.yml`

Gate behavior:

- Triggers on push/PR for `linux-port` and `linux-port/**`.
- Runs `uv run --no-project python tests/linuxPortUnitRunner.py`.
- Avoids the full NVDA Windows lint/unit harness until the Linux port branch has the required native build artifacts and full dependency setup.

This keeps early branch quality checks fast and focused while deeper Linux system testing and full NVDA parity gates are still being built.
