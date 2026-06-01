# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from dataclasses import dataclass
import importlib
import shutil
import sys
from typing import Any, Callable, Mapping


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
	checkX11RecordExtension: Callable[[], tuple[bool, str]] | None = None,
	checkAtspiDesktop: Callable[[], tuple[bool, str]] | None = None,
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
		checkX11RecordExtension=checkX11RecordExtension,
	)
	pyatspi = _checkImport("pyatspi", "AT-SPI2 Python bindings", importModule)
	atspiDesktop = (
		_checkAtspiDesktop(checkAtspiDesktop)
		if pyatspi.available
		else PreflightCheck("atspiDesktop", False, True, "Install AT-SPI2 Python bindings first")
	)
	return (
		PreflightCheck("linux", isLinux, True, platform),
		PreflightCheck(
			"desktopSession",
			bool(sessionName),
			True,
			sessionName or "Set WAYLAND_DISPLAY or DISPLAY",
		),
		pyatspi,
		atspiDesktop,
		_checkImport("wx", "wxPython for settings UI", importModule, required=False),
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
	*,
	required: bool = True,
) -> PreflightCheck:
	try:
		importModule(name)
	except ImportError:
		return PreflightCheck(name, False, required, f"Install {detail}")
	return PreflightCheck(name, True, required, detail)


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
	checkX11RecordExtension: Callable[[], tuple[bool, str]] | None,
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
	if checkX11RecordExtension is None:
		checkX11RecordExtension = _checkX11RecordExtension
	recordAvailable, recordDetail = checkX11RecordExtension()
	if not recordAvailable:
		return PreflightCheck(
			"globalMouseObservation",
			False,
			False,
			recordDetail,
		)
	return PreflightCheck(
		"globalMouseObservation",
		True,
		False,
		"X11 RECORD pointer observation available; validate behavior on desktop",
	)


def _checkX11RecordExtension() -> tuple[bool, str]:
	display: Any | None = None
	try:
		displayModule = importlib.import_module("Xlib.display")
		display = displayModule.Display()
		if not display.has_extension("RECORD"):
			return False, "X11 RECORD extension is unavailable"
	except Exception as error:
		return False, f"Unable to inspect X11 RECORD extension: {error}"
	finally:
		if display is not None:
			try:
				display.close()
			except Exception:
				pass
	return True, "X11 RECORD extension available"


def _checkAtspiDesktop(
	checkAtspiDesktop: Callable[[], tuple[bool, str]] | None,
) -> PreflightCheck:
	if checkAtspiDesktop is None:
		checkAtspiDesktop = _probeAtspiDesktop
	available, detail = checkAtspiDesktop()
	return PreflightCheck("atspiDesktop", available, True, detail)


def _probeAtspiDesktop() -> tuple[bool, str]:
	try:
		pyatspi = importlib.import_module("pyatspi")
		desktopCount = int(pyatspi.Registry.getDesktopCount())
	except Exception as error:
		return False, f"Unable to access AT-SPI desktop registry: {error}"
	if desktopCount <= 0:
		return False, "AT-SPI desktop registry did not expose a desktop"
	return True, f"AT-SPI desktop registry exposed {desktopCount} desktop(s)"
