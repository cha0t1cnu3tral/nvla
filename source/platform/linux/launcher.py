# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from collections.abc import Callable, Sequence
import os
from pathlib import Path
import sys

from .preflight import formatPreflightReport, isReadyForPreview, runPreflightChecks


def runLinuxPreview(
	*,
	sourceDir: Path,
	args: Sequence[str] = (),
	preflight: Callable[[], tuple] = runPreflightChecks,
	coreMain: Callable[[], None] | None = None,
	write: Callable[[str], None] = print,
) -> int:
	"""Run the early Linux preview or report the first actionable blocker."""

	checks = preflight()
	write(formatPreflightReport(checks))
	if not isReadyForPreview(checks):
		write("\nLinux preview dependencies are incomplete.")
		return 1
	sourceDir = sourceDir.resolve()
	os.chdir(sourceDir)
	if str(sourceDir) not in sys.path:
		sys.path.insert(0, str(sourceDir))
	try:
		if coreMain is None:
			coreMain = _loadCoreMain(args)
		coreMain()
	except ImportError as error:
		write(f"\nLinux core handoff is blocked by missing import: {error}")
		return 2
	except Exception as error:
		write(f"\nLinux core handoff failed: {error}")
		return 3
	return 0


def _loadCoreMain(args: Sequence[str]) -> Callable[[], None]:
	"""Initialize the minimum global launcher state before loading NVDA core."""

	import globalVars

	globalVars.appDir = os.getcwd()
	globalVars.appPid = os.getpid()
	globalVars.unknownAppArgs = list(args)
	import NVDAState

	NVDAState._initializeStartTime()
	import languageHandler

	languageHandler.setLanguage("en")
	import core

	return core.main
