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
- Linux user-release roadmap and shortcut-parity audit

## Focused validation

The full NVDA unit harness currently requires built Windows helper DLLs. For dependency-light Linux-port work, run:

```bash
python tests/linuxPortUnitRunner.py
```

This runner installs narrow test stubs and runs the focused Linux-port tests
without loading `nvdaHelperLocal.dll`. The Linux-port gate executes it on
Windows and Ubuntu. On Windows, select the managed interpreter used by CI with:

```powershell
uv run --no-project python tests/linuxPortUnitRunner.py
```

## Linux preview preflight

On a Linux desktop, check the early preview dependencies with:

```bash
python tools/runLinuxPortPreflight.py
```

The command checks the desktop session, AT-SPI2 desktop registry, wxPython,
Linux speech commands, and optional X11 keyboard and pointer capture support
through `python-xlib`. Wayland global capture and full X11 pass-through parity
remain pending.

From an X11 desktop session, verify live keyboard observation with:

```bash
python tools/runLinuxKeyboardSmoke.py --duration 30
```

To exercise X11 NVDA-modifier command suppression and replay, run:

```bash
python tools/runLinuxKeyboardSmoke.py --command-grabs --duration 30
```

Verify live AT-SPI focus events and command-backed speech with:

```bash
python tools/runLinuxFocusSpeechSmoke.py --duration 30
```

Verify live X11 pointer observation with:

```bash
python tools/runLinuxMouseSmoke.py --duration 30
```

Run the native preview launcher with:

```bash
bash tools/runLinuxPort.sh
```

The launcher runs preflight first and then starts the dependency-light native
preview runtime instead of loading the Windows-only `source/nvda.pyw` entry
point. Press `NVDA+H` for supported commands and `NVDA+Q` to exit cleanly.

Run the bounded X11 release workflow and write a reviewable validation report
with:

```bash
python tools/runLinuxReleaseSmoke.py --strict-capture --duration 30 --report linux-preview-smoke.md
```

Preview packaging and user-level install instructions are available in
`packaging/linux/README.md`.

The current release-readiness audit is available in
`dev/linux-preview-release-readiness.md`.

The full user-release target and shortcut-parity workflow are documented in
`dev/linux-user-release-roadmap.md`.
