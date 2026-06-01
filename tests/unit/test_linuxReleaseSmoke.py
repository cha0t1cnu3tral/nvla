# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from datetime import datetime, timezone
import unittest
from unittest import mock

from platform.linux.preflight import PreflightCheck
from platform.linux.release_smoke import formatReleaseSmokeReport, runReleaseSmoke


_READY_CHECKS = (
	PreflightCheck("linux", True, True, "linux"),
	PreflightCheck("speech", True, True, "spd-say"),
)


class TestLinuxReleaseSmoke(unittest.TestCase):
	def test_formats_durable_markdown_report(self):
		report = formatReleaseSmokeReport(
			output=("preflight", "completed"),
			exitStatus=0,
			durationSeconds=30,
			strictCapture=True,
			generatedAt=datetime(2026, 6, 1, 12, 30, tzinfo=timezone.utc),
		)

		self.assertIn("- Generated: `2026-06-01T12:30:00+00:00`", report)
		self.assertIn("- Result: `PASS`", report)
		self.assertIn("- Capture validation: `strict`", report)
		self.assertIn("- [ ] Press NVDA+T", report)
		self.assertIn("```text\npreflight\ncompleted\n```", report)

	def test_formats_failed_fallback_allowed_report(self):
		report = formatReleaseSmokeReport(
			output=(),
			exitStatus=1,
			durationSeconds=15,
			strictCapture=False,
			generatedAt=datetime(2026, 6, 1, tzinfo=timezone.utc),
		)

		self.assertIn("- Result: `FAIL`", report)
		self.assertIn("- Exit status: `1`", report)
		self.assertIn("- Capture validation: `fallback allowed`", report)

	def test_runs_bounded_preview_after_ready_preflight(self):
		runPreview = mock.Mock(return_value=0)
		output = []

		result = runReleaseSmoke(
			durationSeconds=15,
			preflight=lambda: _READY_CHECKS,
			runPreview=runPreview,
			write=output.append,
		)

		self.assertEqual(0, result)
		runPreview.assert_called_once_with(durationSeconds=15, write=output.append)
		self.assertTrue(any("NVDA+T" in line for line in output))
		self.assertTrue(any("Record the manual checklist results" in line for line in output))

	def test_does_not_start_preview_when_required_dependency_is_missing(self):
		runPreview = mock.Mock()
		output = []

		result = runReleaseSmoke(
			preflight=lambda: (PreflightCheck("linux", False, True, "win32"),),
			runPreview=runPreview,
			write=output.append,
		)

		self.assertEqual(1, result)
		runPreview.assert_not_called()
		self.assertIn("not started", output[-1])

	def test_propagates_native_preview_failure(self):
		output = []

		result = runReleaseSmoke(
			preflight=lambda: _READY_CHECKS,
			runPreview=lambda **kwargs: 2,
			write=output.append,
		)

		self.assertEqual(2, result)
		self.assertIn("status 2", output[-1])

	def test_warns_but_runs_when_optional_capture_is_unavailable(self):
		runPreview = mock.Mock(return_value=0)
		output = []
		checks = (
			*_READY_CHECKS,
			PreflightCheck("globalKeyboardCapture", False, False, "local-only"),
		)

		result = runReleaseSmoke(
			preflight=lambda: checks,
			runPreview=runPreview,
			write=output.append,
		)

		self.assertEqual(0, result)
		runPreview.assert_called_once()
		self.assertTrue(any("WARNING: globalKeyboardCapture" in line for line in output))

	def test_strict_capture_does_not_start_preview_when_capture_is_unavailable(self):
		runPreview = mock.Mock()
		output = []
		checks = (
			*_READY_CHECKS,
			PreflightCheck("globalMouseObservation", False, False, "RECORD unavailable"),
		)

		result = runReleaseSmoke(
			strictCapture=True,
			preflight=lambda: checks,
			runPreview=runPreview,
			write=output.append,
		)

		self.assertEqual(1, result)
		runPreview.assert_not_called()
		self.assertIn("Strict capture validation failed", output[-1])

	def test_strict_capture_is_enforced_again_by_native_runtime(self):
		runPreview = mock.Mock(return_value=0)
		checks = (
			*_READY_CHECKS,
			PreflightCheck("globalKeyboardCapture", True, False, "available"),
			PreflightCheck("globalMouseObservation", True, False, "available"),
		)

		result = runReleaseSmoke(
			strictCapture=True,
			preflight=lambda: checks,
			runPreview=runPreview,
			write=lambda text: None,
		)

		self.assertEqual(0, result)
		runPreview.assert_called_once()
		self.assertTrue(runPreview.call_args.kwargs["requireGlobalCapture"])


if __name__ == "__main__":
	unittest.main()
