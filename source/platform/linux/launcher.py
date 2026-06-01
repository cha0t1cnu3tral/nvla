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
	coreMain: Callable[[], int | None] | None = None,
	write: Callable[[str], None] = print,
) -> int:
	"""Run the Linux-native preview after checking desktop dependencies."""

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
			coreMain = _loadNativePreviewMain(args)
		result = coreMain()
		if isinstance(result, int):
			return result
	except ImportError as error:
		write(f"\nLinux preview startup is blocked by missing import: {error}")
		return 2
	except Exception as error:
		write(f"\nLinux preview startup failed: {error}")
		return 3
	return 0


def _loadNativePreviewMain(args: Sequence[str]) -> Callable[[], int | None]:
	if args:
		raise ValueError(f"Unsupported Linux preview arguments: {' '.join(args)}")
	from .preview_runtime import runNativePreview

	return runNativePreview
