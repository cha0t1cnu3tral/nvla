# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
import importlib
import shutil
import sys
from typing import Callable, Mapping


@dataclass(frozen=True)
class PreflightCheck:
	name: str
	available: bool
	required: bool
	detail: str


def runPreflightChecks(
	*,
	platform: str = sys.platform,
	environ: Mapping[str, str] | None = None,
	which: Callable[[str], str | None] = shutil.which,
	importModule: Callable[[str], object] = importlib.import_module,
) -> tuple[PreflightCheck, ...]:
	if environ is None:
		import os

		environ = os.environ
	isLinux = platform.startswith("linux")
	sessionName = (
		"Wayland"
		if environ.get("WAYLAND_DISPLAY")
		else "X11"
		if environ.get("DISPLAY")
		else ""
	)
	speechCommand = next(
		(command for command in ("spd-say", "espeak-ng") if which(command) is not None),
		None,
	)
	audioCommand = next(
		(command for command in ("pw-play", "paplay", "aplay") if which(command) is not None),
		None,
	)
	clipboardCandidates = [
		("xclip", ("xclip",)),
		("xsel", ("xsel",)),
	]
	if environ.get("WAYLAND_DISPLAY"):
		clipboardCandidates.insert(0, ("wl-clipboard", ("wl-copy", "wl-paste")))
	clipboardCommand = next(
		(
			name
			for name, commands in clipboardCandidates
			if all(which(command) is not None for command in commands)
		),
		None,
	)
	globalKeyboardCapture = _checkGlobalKeyboardCapture(
		environ=environ,
		importModule=importModule,
	)
	globalMouseObservation = _checkGlobalMouseObservation(
		environ=environ,
		importModule=importModule,
	)
	return (
		PreflightCheck("linux", isLinux, True, platform),
		PreflightCheck(
			"desktopSession",
			bool(sessionName),
			True,
			sessionName or "Set WAYLAND_DISPLAY or DISPLAY",
		),
		_checkImport("pyatspi", "AT-SPI2 Python bindings", importModule),
		_checkImport("wx", "wxPython", importModule),
		PreflightCheck(
			"speech",
			speechCommand is not None,
			True,
			speechCommand or "Install speech-dispatcher or espeak-ng",
		),
		PreflightCheck(
			"audio",
			audioCommand is not None,
			False,
			audioCommand or "Install PipeWire, PulseAudio, or ALSA command-line tools for waves and tones",
		),
		PreflightCheck(
			"clipboard",
			clipboardCommand is not None,
			False,
			clipboardCommand or "Install wl-clipboard, xclip, or xsel for text clipboard support",
		),
		globalKeyboardCapture,
		globalMouseObservation,
	)


def isReadyForPreview(checks: tuple[PreflightCheck, ...]) -> bool:
	return all(check.available for check in checks if check.required)


def formatPreflightReport(checks: tuple[PreflightCheck, ...]) -> str:
	lines = []
	for check in checks:
		status = "OK" if check.available else "MISSING" if check.required else "PENDING"
		lines.append(f"[{status}] {check.name}: {check.detail}")
	return "\n".join(lines)


def _checkImport(
	name: str,
	detail: str,
	importModule: Callable[[str], object],
) -> PreflightCheck:
	try:
		importModule(name)
	except ImportError:
		return PreflightCheck(name, False, True, f"Install {detail}")
	return PreflightCheck(name, True, True, detail)


def _checkGlobalKeyboardCapture(
	*,
	environ: Mapping[str, str],
	importModule: Callable[[str], object],
) -> PreflightCheck:
	if environ.get("WAYLAND_DISPLAY"):
		return PreflightCheck(
			"globalKeyboardCapture",
			False,
			False,
			"Wayland global capture is not implemented yet; preview remains local-only",
		)
	if not environ.get("DISPLAY"):
		return PreflightCheck(
			"globalKeyboardCapture",
			False,
			False,
			"Set DISPLAY for X11 global observation",
		)
	try:
		importModule("Xlib")
	except ImportError:
		return PreflightCheck(
			"globalKeyboardCapture",
			False,
			False,
			"Install python3-xlib for X11 global observation",
		)
	return PreflightCheck(
		"globalKeyboardCapture",
		True,
		False,
		"X11 NVDA-modifier command grabs available; validate pass-through behavior on desktop",
	)


def _checkGlobalMouseObservation(
	*,
	environ: Mapping[str, str],
	importModule: Callable[[str], object],
) -> PreflightCheck:
	if environ.get("WAYLAND_DISPLAY"):
		return PreflightCheck(
			"globalMouseObservation",
			False,
			False,
			"Wayland global observation is not implemented yet",
		)
	if not environ.get("DISPLAY"):
		return PreflightCheck(
			"globalMouseObservation",
			False,
			False,
			"Set DISPLAY for X11 global observation",
		)
	try:
		importModule("Xlib")
	except ImportError:
		return PreflightCheck(
			"globalMouseObservation",
			False,
			False,
			"Install python3-xlib for X11 global observation",
		)
	return PreflightCheck(
		"globalMouseObservation",
		True,
		False,
		"X11 RECORD pointer observation available; validate behavior on desktop",
	)
