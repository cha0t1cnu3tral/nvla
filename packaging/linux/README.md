# NVDA Linux Preview Packaging

This directory contains user-level preview packaging artifacts. They expose the
Linux-native launcher without using the Windows `source/nvda.pyw` entry point.

## Required runtime packages

Install Python 3, AT-SPI2 Python bindings, wxPython, and one supported speech
command. Package names differ by distribution.

Ubuntu:

```bash
sudo apt install python3 python3-pyatspi python3-wxgtk4.0 speech-dispatcher
```

Fedora:

```bash
sudo dnf install python3 python3-pyatspi python3-wxpython4 speech-dispatcher
```

`espeak-ng` can replace Speech Dispatcher as the initial speech fallback.

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
reports the first remaining bootstrap blocker. Global X11 and Wayland keyboard
capture, full browse-mode wiring, Linux audio beyond command speech output,
and real desktop validation remain incomplete.
