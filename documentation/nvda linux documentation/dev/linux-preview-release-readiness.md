# Linux Preview Release Readiness

Last updated: 2026-06-01

## Current result

The Linux port is not a complete `0.1` screen-reader release yet. It has a
dependency-light native preview runtime and user-level packaging artifacts,
but it should still be treated as a bring-up tool.

## Implemented without Linux desktop testing

- Linux-native preflight and launcher paths that avoid `source/nvda.pyw`.
- Preflight probes for an accessible AT-SPI desktop registry and X11 RECORD
  support so release-smoke failures are reported before runtime startup.
- A Linux-native preview runtime loop that combines AT-SPI focus announcements,
  document-navigation speech, keyboard capture, and pointer observation without
  loading the incomplete shared core.
- Native `NVDA+1`, `NVDA+F12`, `NVDA+T`, `NVDA+Tab`, `NVDA+B`, `NVDA+H`, and
  `NVDA+Q` preview commands for input help, time and date, the active window
  title, focused object, a bounded active-tree read-through, command help, and
  clean preview shutdown.
- Linux-compatible shared bootstrap fallbacks for registry, argument parsing,
  logging, localization, queue watchdog selection, configuration, and add-on
  bundle decoding.
- AT-SPI event translation, coalescing, object wrappers, geometry, caret and
  selection handling, and baseline text review primitives.
- A Linux-local AT-SPI object base that avoids importing the Windows-heavy
  shared `NVDAObjects` package during native backend construction.
- Keyboard gesture normalization that reuses the existing NVDA `kb:` command
  identifiers, including NVDA modifier behavior and pass-through intent.
- X11 RECORD-based global keyboard observation through `python-xlib`. This
  supports live diagnostic output without suppressing handled keys.
- X11 synchronous passive grabs for configured NVDA modifier keys. This
  suppresses handled preview commands and replays unhandled events, but still
  requires desktop validation for exact pass-through parity.
- Linux `/proc` process enumeration and X11 EWMH desktop, active-window, and
  client-list discovery behind the process-focus PAL boundary.
- An X11 keyboard smoke tool that reports live normalized gestures through the
  RECORD observer and can exercise NVDA-modifier command suppression and replay.
- X11 RECORD-based global pointer observation plus a mouse smoke tool that
  reports live motion and button events without loading the Windows mouse stack.
- Linux-native pointer tracking groundwork that resolves observed X11 motion
  through AT-SPI hit testing and bridges accessible objects to mouse-move
  dispatch through the dependency-light native event dispatcher.
- A dependency-light Linux event dispatcher for cached focus and mouse state,
  allowing AT-SPI and pointer bridges to avoid importing shared Win32-heavy
  `api` and `eventHandler` modules during Linux adapter construction.
- An audible AT-SPI focus smoke tool that speaks live focused-object names,
  descriptions, and roles without requiring the incomplete core startup path.
- Command-backed speech output using Speech Dispatcher or `espeak-ng`.
- Command-backed Linux wave and generated-tone playback using `pw-play`,
  `paplay`, or `aplay`.
- Command-backed text clipboard access using `wl-clipboard`, `xclip`, or
  `xsel`.
- Document navigation primitives for line movement and quick navigation by
  headings, links, controls, lists, tables, and landmarks.
- A Linux preview document-navigation controller that activates for focused
  AT-SPI documents, consumes line and supported single-letter browse keys,
  and announces the resulting text.
- A preview shell launcher, installer, uninstaller, desktop entry, and
  optional systemd user service.
- An Ubuntu CI packaging smoke that installs to custom XDG directories,
  validates rendered launcher paths, and removes the user-level artifacts.
- A dependency-light focused Python test runner exercised on Windows and
  native Ubuntu CI without building the Windows helper stack.
- A bounded release-smoke runner that gates on preflight and prints the manual
  X11 validation checklist around a native preview run.
- Strict release-smoke capture gating for X11 validation runs that must not
  silently degrade to local-only keyboard or pointer handling.
- Optional Markdown release-smoke reports with run metadata, the console
  transcript, and an unchecked desktop-validation checklist.
- A user-facing Linux preview guide covering commands, installation, strict
  smoke validation, supported sessions, and known limitations.
- A shortcut-parity audit that inventories the shared Windows keyboard map and
  distinguishes identifier translation from executable native runtime scripts.

## Remaining non-desktop implementation work

- Continue separating shared startup imports that still assume the full
  Windows-oriented object, GUI, braille, and display stack.
- Replace command-backed preview audio with a streaming Linux audio backend.
- Deepen Linux mouse behavior beyond accessible-object tracking, add touch
  support, and define Wayland process-focus and pointer strategies.
- Add brlapi integration and Linux device discovery.
- Define a production package dependency strategy before adding Flatpak,
  `.deb`, or `.rpm` release manifests.

## Work that requires Linux desktop execution

- Validate X11 NVDA-modifier command suppression and pass-through replay
  against real desktop applications.
- Define, implement, and validate the Wayland capture strategy.
- Verify AT-SPI focus, caret, property, and document events against real apps
  and browsers.
- Verify Speech Dispatcher and `espeak-ng` behavior in a graphical session.
- Run end-to-end keyboard, browse navigation, startup service, desktop entry,
  and shutdown smoke tests.
