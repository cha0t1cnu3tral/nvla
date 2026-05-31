# NVDA Linux Preview Packaging

This directory contains user-level preview packaging artifacts. They expose the
Linux-native launcher without using the Windows `source/nvda.pyw` entry point.

## Required runtime packages

Install Python 3, AT-SPI2 Python bindings, wxPython, one supported speech
command, and a command-line audio player. Package names differ by distribution.

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

## Current limitations

This is not a usable release yet. The launcher runs dependency preflight and
reports the first remaining bootstrap blocker. X11 can observe global keys
through the RECORD extension, but handled keys still reach the focused
application. Wayland global capture, full browse-mode wiring, streaming Linux
audio, and real desktop validation remain incomplete.
