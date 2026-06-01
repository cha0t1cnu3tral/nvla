# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from platform.linux import launcher
from platform.linux.launcher import runLinuxPreview
from platform.linux.preflight import PreflightCheck


_READY_CHECKS = (
	PreflightCheck("linux", True, True, "linux"),
	PreflightCheck("speech", True, True, "spd-say"),
	PreflightCheck("globalKeyboardCapture", False, False, "pending"),
)


class TestLinuxLauncher(unittest.TestCase):
	def test_rejects_incomplete_preflight(self):
		messages = []
		checks = (PreflightCheck("linux", False, True, "win32"),)

		result = runLinuxPreview(
			sourceDir=Path("."),
			preflight=lambda: checks,
			coreMain=mock.Mock(),
			write=messages.append,
		)

		self.assertEqual(1, result)
		self.assertIn("dependencies are incomplete", messages[-1])

	def test_runs_injected_main_after_ready_preflight(self):
		messages = []
		coreMain = mock.Mock()
		with tempfile.TemporaryDirectory() as directory:
			originalDirectory = os.getcwd()
			try:
				result = runLinuxPreview(
					sourceDir=Path(directory),
					preflight=lambda: _READY_CHECKS,
					coreMain=coreMain,
					write=messages.append,
				)
			finally:
				os.chdir(originalDirectory)

		self.assertEqual(0, result)
		coreMain.assert_called_once_with()

	def test_returns_native_preview_status(self):
		with tempfile.TemporaryDirectory() as directory:
			originalDirectory = os.getcwd()
			try:
				result = runLinuxPreview(
					sourceDir=Path(directory),
					preflight=lambda: _READY_CHECKS,
					coreMain=lambda: 2,
					write=lambda message: None,
				)
			finally:
				os.chdir(originalDirectory)

		self.assertEqual(2, result)

	def test_loads_native_preview_main_by_default(self):
		previewMain = mock.Mock()
		messages = []
		with tempfile.TemporaryDirectory() as directory:
			originalDirectory = os.getcwd()
			try:
				with mock.patch.object(launcher, "_loadNativePreviewMain", return_value=previewMain) as loadMain:
					result = runLinuxPreview(
						sourceDir=Path(directory),
						preflight=lambda: _READY_CHECKS,
						write=messages.append,
					)
			finally:
				os.chdir(originalDirectory)

		self.assertEqual(0, result)
		loadMain.assert_called_once_with(())
		previewMain.assert_called_once_with()

	def test_reports_missing_preview_import(self):
		messages = []

		def failCore():
			raise ImportError("winBindings.kernel32")

		with tempfile.TemporaryDirectory() as directory:
			originalDirectory = os.getcwd()
			try:
				result = runLinuxPreview(
					sourceDir=Path(directory),
					preflight=lambda: _READY_CHECKS,
					coreMain=failCore,
					write=messages.append,
				)
			finally:
				os.chdir(originalDirectory)

		self.assertEqual(2, result)
		self.assertIn("winBindings.kernel32", messages[-1])


if __name__ == "__main__":
	unittest.main()
