# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import unittest
from types import SimpleNamespace
from unittest import mock

from platform.linux import preflight
from platform.linux.preflight import formatPreflightReport, isReadyForPreview, runPreflightChecks


class TestLinuxPreflight(unittest.TestCase):
	def test_reports_ready_preview_dependencies(self):
		checks = runPreflightChecks(
			platform="linux",
			environ={"DISPLAY": ":1"},
			which=lambda command: f"/usr/bin/{command}" if command == "spd-say" else None,
			importModule=lambda name: object(),
			checkX11RecordExtension=lambda: (True, "available"),
		)

		self.assertTrue(isReadyForPreview(checks))
		self.assertIn("[OK] desktopSession: X11", formatPreflightReport(checks))
		self.assertIn("[PENDING] audio:", formatPreflightReport(checks))
		self.assertIn("[PENDING] clipboard:", formatPreflightReport(checks))
		self.assertIn("[OK] globalKeyboardCapture: X11 NVDA-modifier command grabs available", formatPreflightReport(checks))
		self.assertIn("[OK] globalMouseObservation: X11 RECORD pointer observation available", formatPreflightReport(checks))

	def test_prefers_speech_dispatcher_before_espeak_ng(self):
		checks = runPreflightChecks(
			platform="linux",
			environ={"WAYLAND_DISPLAY": "wayland-0"},
			which=lambda command: f"/usr/bin/{command}",
			importModule=lambda name: object(),
		)

		speech = next(check for check in checks if check.name == "speech")
		audio = next(check for check in checks if check.name == "audio")
		clipboard = next(check for check in checks if check.name == "clipboard")
		self.assertEqual("spd-say", speech.detail)
		self.assertEqual("pw-play", audio.detail)
		self.assertEqual("wl-clipboard", clipboard.detail)
		globalKeyboardCapture = next(check for check in checks if check.name == "globalKeyboardCapture")
		self.assertFalse(globalKeyboardCapture.available)
		self.assertIn("Wayland", globalKeyboardCapture.detail)
		globalMouseObservation = next(check for check in checks if check.name == "globalMouseObservation")
		self.assertFalse(globalMouseObservation.available)
		self.assertIn("Wayland", globalMouseObservation.detail)

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
		self.assertIn("[PENDING] wx:", report)
		self.assertIn("[MISSING] speech:", report)

	def test_reports_missing_optional_python_xlib_for_x11_capture(self):
		def importModule(name):
			if name == "Xlib":
				raise ImportError(name)
			return object()

		checks = runPreflightChecks(
			platform="linux",
			environ={"DISPLAY": ":1"},
			which=lambda command: "/usr/bin/spd-say" if command == "spd-say" else None,
			importModule=importModule,
		)

		globalKeyboardCapture = next(check for check in checks if check.name == "globalKeyboardCapture")
		self.assertFalse(globalKeyboardCapture.available)
		self.assertFalse(globalKeyboardCapture.required)
		self.assertIn("python3-xlib", globalKeyboardCapture.detail)
		globalMouseObservation = next(check for check in checks if check.name == "globalMouseObservation")
		self.assertFalse(globalMouseObservation.available)
		self.assertFalse(globalMouseObservation.required)
		self.assertIn("python3-xlib", globalMouseObservation.detail)

	def test_reports_missing_optional_x11_record_extension_for_mouse_observation(self):
		checks = runPreflightChecks(
			platform="linux",
			environ={"DISPLAY": ":1"},
			which=lambda command: "/usr/bin/spd-say" if command == "spd-say" else None,
			importModule=lambda name: object(),
			checkX11RecordExtension=lambda: (False, "X11 RECORD extension is unavailable"),
		)

		globalKeyboardCapture = next(check for check in checks if check.name == "globalKeyboardCapture")
		globalMouseObservation = next(check for check in checks if check.name == "globalMouseObservation")
		self.assertTrue(globalKeyboardCapture.available)
		self.assertFalse(globalMouseObservation.available)
		self.assertIn("RECORD extension is unavailable", globalMouseObservation.detail)

	def test_x11_record_probe_closes_display(self):
		display = SimpleNamespace(
			has_extension=mock.Mock(return_value=True),
			close=mock.Mock(),
		)
		with mock.patch.object(
			preflight.importlib,
			"import_module",
			return_value=SimpleNamespace(Display=lambda: display),
		):
			available, detail = preflight._checkX11RecordExtension()

		self.assertTrue(available)
		self.assertIn("available", detail)
		display.close.assert_called_once_with()

	def test_x11_record_probe_reports_missing_extension_and_closes_display(self):
		display = SimpleNamespace(
			has_extension=mock.Mock(return_value=False),
			close=mock.Mock(),
		)
		with mock.patch.object(
			preflight.importlib,
			"import_module",
			return_value=SimpleNamespace(Display=lambda: display),
		):
			available, detail = preflight._checkX11RecordExtension()

		self.assertFalse(available)
		self.assertIn("unavailable", detail)
		display.close.assert_called_once_with()


if __name__ == "__main__":
	unittest.main()
