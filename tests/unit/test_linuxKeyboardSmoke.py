# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

from platform.linux.keyboard_smoke import runKeyboardSmoke


class _SmokeKeyboardSource:
	supportsPassThroughEnforcement = False

	def __init__(self, *, fail=False):
		self.fail = fail
		self.isStopped = False

	def start(self, emit):
		if self.fail:
			raise RuntimeError("record unavailable")
		emit(SimpleNamespace(key="a", pressed=True))
		emit(SimpleNamespace(key="a", pressed=False))

	def stop(self):
		self.isStopped = True


class _SmokeCommandGrabSource(_SmokeKeyboardSource):
	supportsHandledGestureSuppression = True

	def start(self, emit):
		emit(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))
		emit(SimpleNamespace(key="t", pressed=True, nvdaModifierKeys=4))
		emit(SimpleNamespace(key="t", pressed=False, nvdaModifierKeys=4))
		emit(SimpleNamespace(key="insert", pressed=False, nvdaModifierKeys=4))


class TestLinuxKeyboardSmoke(unittest.TestCase):
	def test_observes_x11_keys_and_stops_source(self):
		source = _SmokeKeyboardSource()
		output = []
		waits = []

		result = runKeyboardSmoke(
			durationSeconds=2,
			environ={"DISPLAY": ":1"},
			source=source,
			wait=waits.append,
			write=output.append,
		)

		self.assertEqual(0, result)
		self.assertEqual([2], waits)
		self.assertTrue(source.isStopped)
		self.assertIn("Keyboard capture mode: globalObserveOnly", output)
		self.assertIn("down: A passThrough", output)
		self.assertIn("up: A passThrough", output)

	def test_rejects_wayland_session(self):
		output = []

		result = runKeyboardSmoke(
			environ={"DISPLAY": ":1", "WAYLAND_DISPLAY": "wayland-0"},
			write=output.append,
		)

		self.assertEqual(1, result)
		self.assertIn("Wayland", output[0])

	def test_command_grab_mode_handles_smoke_chord(self):
		source = _SmokeCommandGrabSource()
		output = []

		result = runKeyboardSmoke(
			durationSeconds=0,
			commandGrabs=True,
			environ={"DISPLAY": ":1"},
			source=source,
			write=output.append,
		)

		self.assertEqual(0, result)
		self.assertTrue(source.isStopped)
		self.assertIn("Keyboard capture mode: globalCommands", output)
		self.assertIn("handled: NVDA+T", output)
		self.assertIn("down: NVDA+T", output)

	def test_reports_x11_start_failure(self):
		source = _SmokeKeyboardSource(fail=True)
		output = []

		result = runKeyboardSmoke(
			environ={"DISPLAY": ":1"},
			source=source,
			write=output.append,
		)

		self.assertEqual(2, result)
		self.assertTrue(source.isStopped)
		self.assertIn("record unavailable", output[-1])


if __name__ == "__main__":
	unittest.main()
