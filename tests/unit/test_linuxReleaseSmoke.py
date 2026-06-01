# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import unittest
from unittest import mock

from platform.linux.preflight import PreflightCheck
from platform.linux.release_smoke import runReleaseSmoke


_READY_CHECKS = (
	PreflightCheck("linux", True, True, "linux"),
	PreflightCheck("speech", True, True, "spd-say"),
)


class TestLinuxReleaseSmoke(unittest.TestCase):
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


if __name__ == "__main__":
	unittest.main()
