# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

from collections.abc import Callable

from .preflight import formatPreflightReport, isReadyForPreview, runPreflightChecks
from .preview_runtime import runNativePreview


_MANUAL_CHECKLIST = (
	"Move focus between controls in another application and confirm spoken focus changes.",
	"Press NVDA+T and confirm the active window title is spoken.",
	"Press NVDA+Tab and confirm the focused control is spoken.",
	"Press NVDA+B and confirm the active accessible tree is read.",
	"Press NVDA+H and confirm the native preview command help is spoken.",
	"Press an unhandled NVDA chord and confirm the focused application still receives it.",
	"Move the pointer over accessible controls and check for capture fallback errors.",
	"Press NVDA+Q before timeout and confirm the preview exits cleanly.",
)
_CAPTURE_CHECK_NAMES = frozenset(("globalKeyboardCapture", "globalMouseObservation"))


def runReleaseSmoke(
	*,
	durationSeconds: float = 30,
	strictCapture: bool = False,
	preflight: Callable[[], tuple] = runPreflightChecks,
	runPreview: Callable[..., int] = runNativePreview,
	write: Callable[[str], None] = print,
) -> int:
	"""Run preflight and a bounded native preview with a manual release checklist."""

	checks = preflight()
	write(formatPreflightReport(checks))
	if not isReadyForPreview(checks):
		write("\nLinux preview dependencies are incomplete. Release smoke was not started.")
		return 1
	missingCaptureChecks = tuple(
		check
		for check in checks
		if check.name in _CAPTURE_CHECK_NAMES and not check.available
	)
	for check in missingCaptureChecks:
		write(f"\nWARNING: {check.name} is unavailable: {check.detail}")
	if strictCapture and missingCaptureChecks:
		write("\nStrict capture validation failed. Release smoke was not started.")
		return 1
	write("\nLinux preview release smoke checklist:")
	for index, item in enumerate(_MANUAL_CHECKLIST, start=1):
		write(f"{index}. {item}")
	write(f"\nStarting a {durationSeconds:g}-second native preview smoke run.")
	previewArgs = {
		"durationSeconds": durationSeconds,
		"write": write,
	}
	if strictCapture:
		previewArgs["requireGlobalCapture"] = True
	result = runPreview(**previewArgs)
	if result != 0:
		write(f"\nLinux preview release smoke failed with status {result}.")
		return result
	write("\nLinux preview release smoke completed. Record the manual checklist results.")
	return 0
