# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import unittest

from platform.linux.preflight import formatPreflightReport, isReadyForPreview, runPreflightChecks


class TestLinuxPreflight(unittest.TestCase):
	def test_reports_ready_preview_dependencies(self):
		checks = runPreflightChecks(
			platform="linux",
			environ={"DISPLAY": ":1"},
			which=lambda command: f"/usr/bin/{command}" if command == "spd-say" else None,
			importModule=lambda name: object(),
		)

		self.assertTrue(isReadyForPreview(checks))
		self.assertIn("[OK] desktopSession: X11", formatPreflightReport(checks))
		self.assertIn("[PENDING] globalKeyboardCapture:", formatPreflightReport(checks))

	def test_prefers_speech_dispatcher_before_espeak_ng(self):
		checks = runPreflightChecks(
			platform="linux",
			environ={"WAYLAND_DISPLAY": "wayland-0"},
			which=lambda command: f"/usr/bin/{command}",
			importModule=lambda name: object(),
		)

		speech = next(check for check in checks if check.name == "speech")
		self.assertEqual("spd-say", speech.detail)

	def test_reports_missing_required_dependencies(self):
		def missingModule(name):
			raise ImportError(name)

		checks = runPreflightChecks(
			platform="win32",
			environ={},
			which=lambda command: None,
			importModule=missingModule,
		)

		self.assertFalse(isReadyForPreview(checks))
		report = formatPreflightReport(checks)
		self.assertIn("[MISSING] linux: win32", report)
		self.assertIn("[MISSING] desktopSession:", report)
		self.assertIn("[MISSING] pyatspi:", report)
		self.assertIn("[MISSING] wx:", report)
		self.assertIn("[MISSING] speech:", report)


if __name__ == "__main__":
	unittest.main()
