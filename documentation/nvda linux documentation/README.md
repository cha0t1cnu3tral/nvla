# NVDA Linux Documentation (Rewrite Track)

This folder stores Linux port planning and implementation notes for the rewrite.

- `dev/`: engineering docs for branch setup, CI gate, target distros, dependency map, and compatibility matrix.
- `user/`: user-facing Linux port status updates.

Current dev milestones documented:

- Phase 0 baseline artifacts
- Phase 1 PAL scaffolding and core import routing
- Phase 2 AT-SPI2 mapping, event translation, object-wrapper, and baseline TextInfo work
- Phase 3 input foundation and Linux keyboard event normalization

## Focused validation on Windows

The full NVDA unit harness currently requires built Windows helper DLLs. For dependency-light Linux-port work, run:

```powershell
uv run python tests/linuxPortUnitRunner.py
```

This runner installs narrow test stubs and runs the AT-SPI mapping/event/object tests without loading `nvdaHelperLocal.dll`.
