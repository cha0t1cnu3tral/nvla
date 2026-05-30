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
			"globalKeyboardCapture",
			False,
			False,
			"Not implemented yet; Linux preview remains local-only",
		),
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
