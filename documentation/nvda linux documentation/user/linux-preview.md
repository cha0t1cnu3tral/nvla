# NVDA Linux Preview

The Linux port is an early `0.1` preview for testing on modern Linux desktops.
It is not yet a replacement for the stable Windows release.

## Supported Preview Path

- X11 is the primary validation target.
- Wayland can start in a restricted local-only mode, but global keyboard and
  pointer capture are not implemented yet.
- Speech output uses Speech Dispatcher through `spd-say`, with `espeak-ng` as
  a fallback.
- Accessibility events and object information come from AT-SPI2.

## Install And Run

From the repository root:

```bash
bash packaging/linux/installPreview.sh
nvda-linux-preview
```

Remove the user-level preview artifacts with:

```bash
bash packaging/linux/uninstallPreview.sh
```

Press `NVDA+Q` to exit cleanly. For a bounded test run:

```bash
nvda-linux-preview --duration 30
```

For X11 release validation:

```bash
python3 tools/runLinuxReleaseSmoke.py --strict-capture --duration 30 --report linux-preview-smoke.md
```

The Markdown report records preflight and runtime output. Mark each manual
checklist item after validating the desktop behavior.

## Native Preview Commands

| Command | Action |
| --- | --- |
| `NVDA+T` | Speak the active window title. |
| `NVDA+Tab` | Speak the focused accessible object. |
| `NVDA+B` | Read a bounded traversal of the active accessible object tree. |
| `NVDA+H` | Speak the supported native preview commands. |
| `NVDA+Q` | Exit the Linux preview cleanly. |

When focus is inside an AT-SPI document, the preview also supports line
navigation with `Up Arrow` and `Down Arrow`, plus supported single-letter quick
navigation keys for headings, links, controls, lists, tables, and landmarks.

## Known Limitations

- X11 keyboard suppression and pass-through still require desktop validation.
- Wayland global keyboard and pointer capture are not implemented.
- Browse mode is intentionally limited and does not match mature NVDA browser
  support.
- Speech launches command-line clients per announcement instead of using a
  persistent Speech Dispatcher connection.
- Wave and tone playback use command-line players instead of a streaming audio
  backend.
- Braille, touch, rich mouse behavior, settings UI, and production Flatpak,
  `.deb`, and `.rpm` packages are not implemented.
- Real desktop testing on Ubuntu and Fedora is still required before publishing
  a `0.1` preview artifact.
