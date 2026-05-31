# Linux Preview Release Readiness

Last updated: 2026-05-31

## Current result

The Linux port is not a usable `0.1` screen-reader release yet. It has a
preview launcher and user-level packaging artifacts, but the launcher should
still be treated as a bring-up tool.

## Implemented without Linux desktop testing

- Linux-native preflight and launcher paths that avoid `source/nvda.pyw`.
- Linux-compatible shared bootstrap fallbacks for registry, argument parsing,
  logging, localization, queue watchdog selection, configuration, and add-on
  bundle decoding.
- AT-SPI event translation, coalescing, object wrappers, geometry, caret and
  selection handling, and baseline text review primitives.
- A Linux-local AT-SPI object base that avoids importing the Windows-heavy
  shared `NVDAObjects` package during native backend construction.
- Keyboard gesture normalization that reuses the existing NVDA `kb:` command
  identifiers, including NVDA modifier behavior and pass-through intent.
- Command-backed speech output using Speech Dispatcher or `espeak-ng`.
- Document navigation primitives for line movement and quick navigation by
  headings, links, controls, lists, tables, and landmarks.
- A preview shell launcher, installer, desktop entry, and optional systemd
  user service.

## Remaining non-desktop implementation work

- Wire Linux document navigation into keyboard scripts and spoken output.
- Replace or separate shared event-dispatch imports that still assume the full
  Windows-oriented object, GUI, braille, and display stack.
- Add Linux-native audio playback for tones and wave output.
- Add clipboard, process-focus, mouse, and touch implementations.
- Add brlapi integration and Linux device discovery.
- Define a production package dependency strategy before adding Flatpak,
  `.deb`, or `.rpm` release manifests.

## Work that requires Linux desktop execution

- Implement and validate global X11 keyboard capture.
- Define, implement, and validate the Wayland capture strategy.
- Verify AT-SPI focus, caret, property, and document events against real apps
  and browsers.
- Verify Speech Dispatcher and `espeak-ng` behavior in a graphical session.
- Run end-to-end keyboard, browse navigation, startup service, desktop entry,
  and shutdown smoke tests.
