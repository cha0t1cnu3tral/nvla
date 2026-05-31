# NVDA Linux Documentation (Rewrite Track)

This folder stores Linux port planning and implementation notes for the rewrite.

- `dev/`: engineering docs for branch setup, CI gate, target distros, dependency map, and compatibility matrix.
- `user/`: user-facing Linux port status updates.

Current dev milestones documented:

- Phase 0 baseline artifacts
- Phase 1 PAL scaffolding and core import routing
- Phase 2 AT-SPI2 mapping, event translation, object-wrapper, and baseline TextInfo work
- Phase 3 input foundation and Linux keyboard event normalization
- Phase 4 Linux speech transport and initial NVDA synth driver
- Linux preview release-readiness audit

## Focused validation on Windows

The full NVDA unit harness currently requires built Windows helper DLLs. For dependency-light Linux-port work, run:

```powershell
uv run --no-project python tests/linuxPortUnitRunner.py
```

This runner installs narrow test stubs and runs the AT-SPI mapping/event/object tests without loading `nvdaHelperLocal.dll`.

## Linux preview preflight

On a Linux desktop, check the early preview dependencies with:

```bash
python tools/runLinuxPortPreflight.py
```

The command checks the desktop session, AT-SPI2 Python bindings, wxPython, Linux speech commands, and optional X11 global keyboard observation through `python-xlib`. Wayland global capture and X11 handled-key suppression remain pending.

From an X11 desktop session, verify live keyboard observation with:

```bash
python tools/runLinuxKeyboardSmoke.py --duration 30
```

Verify live AT-SPI focus events and command-backed speech with:

```bash
python tools/runLinuxFocusSpeechSmoke.py --duration 30
```

Run the early launcher with:

```bash
bash tools/runLinuxPort.sh
```

The launcher runs preflight first and then attempts the Linux core handoff. During bring-up, it reports the first remaining missing import instead of loading the Windows-only `source/nvda.pyw` entry point.

Preview packaging and user-level install instructions are available in
`packaging/linux/README.md`.

The current release-readiness audit is available in
`dev/linux-preview-release-readiness.md`.
