# Linux User Release Roadmap

Last updated: 2026-06-01

## Target

The release target is a smooth daily-use Linux screen reader, not a restricted
preview. Every existing Windows keyboard shortcut must keep the same binding
and produce equivalent Linux behavior wherever the operating system exposes
the required capability. Linux must not substitute an alternate shortcut table
for commands that already have Windows bindings.

## Shortcut Parity Model

Linux keyboard normalization already emits the shared `kb:` identifiers used
by NVDA's Windows command maps. This avoids maintaining a separate Linux
shortcut table.

Run the shortcut audit with:

```bash
python tools/runLinuxShortcutParityAudit.py --output linux-shortcut-parity.md
```

The report separates identifier translation coverage from native runtime
execution coverage. A shortcut is release-ready only when its script and all
required subsystems work smoothly on Linux, including physical capture,
pass-through behavior, spoken output, and desktop validation.

Baseline on 2026-06-01:

- Shared built-in keyboard identifiers translated by Linux input: `163/163`.
- Shared identifiers handled by the dependency-light native preview: `8/163`.
- Shared identifiers still waiting for shared-runtime integration: `155/163`.

## Release Requirements

1. Port shared startup far enough to execute the existing global command map.
2. Validate every built-in desktop and laptop keyboard binding on X11.
3. Implement and validate a Wayland-compatible global shortcut strategy.
4. Complete AT-SPI review, browse-mode, focus, caret, formatting, and embedded
   object behavior for common desktop applications and browsers.
5. Replace preview command-backed audio with persistent speech and streaming
   Linux audio backends.
6. Add braille through brlapi, touch gestures, richer mouse behavior, settings
   UI, add-on workflows, and Linux device discovery.
7. Ship production Flatpak, `.deb`, and `.rpm` packaging with upgrade and
   uninstall paths.
8. Add graphical Linux system tests and complete Ubuntu and Fedora release
   validation.
