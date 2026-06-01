# NVDA Linux Preview Packaging

This directory contains user-level preview packaging artifacts. They expose the
Linux-native launcher without using the Windows `source/nvda.pyw` entry point.

See `documentation/nvda linux documentation/user/linux-preview.md` for the
user-facing preview commands and limitations.

## Required runtime packages

Install Python 3, AT-SPI2 Python bindings, one supported speech command, and a
command-line audio player. wxPython is recommended for future settings UI work.
Package names differ by distribution.

Ubuntu:

```bash
sudo apt install python3 python3-pyatspi python3-wxgtk4.0 python3-xlib speech-dispatcher pipewire-bin
```

Fedora:

```bash
sudo dnf install python3 python3-pyatspi python3-wxpython4 python3-xlib speech-dispatcher pipewire-utils
```

`espeak-ng` can replace Speech Dispatcher as the initial speech fallback.
`paplay` or `aplay` can replace `pw-play` for preview wave and tone playback.
Install `wl-clipboard`, `xclip`, or `xsel` to enable preview text clipboard
integration.

## Install the preview launcher

From the repository root:

```bash
bash packaging/linux/installPreview.sh
nvda-linux-preview
```

The installer also places an optional systemd user service. Enable it only
after manual startup succeeds:

```bash
systemctl --user enable --now nvda-linux-preview.service
```

Remove the user-level preview launcher, desktop entry, and optional service
with:

```bash
bash packaging/linux/uninstallPreview.sh
```

The native preview announces AT-SPI focus changes. Press `NVDA+1` for input
help, `NVDA+C` for clipboard text, `NVDA+F2` to pass the next physical key
sequence through, `NVDA+F12` for the time or date, `NVDA+T` for the active
window title, `NVDA+Tab` for the focused object, and `NVDA+B` to read through
the active accessible object tree. Press `NVDA+H` for native preview command
help and `NVDA+Q` to exit cleanly.

For a time-bounded full preview smoke run:

```bash
nvda-linux-preview --duration 30
```

For the release-oriented preflight, runtime, and manual validation checklist:

```bash
python3 tools/runLinuxReleaseSmoke.py --duration 30
```

For X11 release validation, require both global keyboard and pointer capture:

```bash
python3 tools/runLinuxReleaseSmoke.py --strict-capture --duration 30 --report linux-preview-smoke.md
```

Review the generated Markdown report and mark each manual checklist item after
the desktop run.

## Test X11 keyboard observation

From an X11 desktop session, confirm that global key events are visible before
running the full preview:

```bash
python3 tools/runLinuxKeyboardSmoke.py --duration 30
```

Press keys while another application has focus. The tool reports normalized
key-down and key-up gestures from the same X11 backend used by the preview.

To exercise the preview's X11 NVDA-modifier command grabs, run:

```bash
python3 tools/runLinuxKeyboardSmoke.py --command-grabs --duration 30
```

Press `NVDA+T` in another application. The tool logs it as handled so its
suppression can be checked. Other NVDA chords exercise pass-through replay.

## Test AT-SPI focus speech

Confirm that focus events and preview speech work together:

```bash
python3 tools/runLinuxFocusSpeechSmoke.py --duration 30
```

Move focus between applications and controls. The tool prints and speaks each
focused object's available name, description, and role.

## Test X11 mouse observation

From an X11 desktop session, confirm that global pointer events are visible:

```bash
python3 tools/runLinuxMouseSmoke.py --duration 30
```

Move and click the pointer in other applications. The tool reports motion and
button events from the preview X11 RECORD backend.

## Current limitations

This is not a complete release yet. The launcher runs dependency preflight and
starts the native preview runtime without loading the incomplete shared core.
X11 can suppress handled NVDA-modifier commands through passive grabs, but exact
pass-through behavior still needs desktop validation. Wayland global capture,
full browse-mode wiring, streaming Linux audio, and real desktop validation
remain incomplete.
