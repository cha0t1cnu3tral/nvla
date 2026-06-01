# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

from platform.linux.mouse_smoke import runMouseSmoke


class _SmokeMouseSource:
	def __init__(self, *, fail=False):
		self.fail = fail
		self.isStopped = False

	def start(self, emit):
		if self.fail:
			raise RuntimeError("record unavailable")
		emit(SimpleNamespace(kind="move", x=10, y=20))
		emit(SimpleNamespace(kind="buttonDown", x=10, y=20, button=1))

	def stop(self):
		self.isStopped = True


class TestLinuxMouseSmoke(unittest.TestCase):
	def test_observes_x11_mouse_events_and_stops_source(self):
		source = _SmokeMouseSource()
		output = []
		waits = []

		result = runMouseSmoke(
			durationSeconds=2,
			environ={"DISPLAY": ":1"},
			source=source,
			wait=waits.append,
			write=output.append,
		)

		self.assertEqual(0, result)
		self.assertEqual([2], waits)
		self.assertTrue(source.isStopped)
		self.assertIn("Mouse capture mode: globalObserveOnly", output)
		self.assertIn("move: x=10 y=20", output)
		self.assertIn("buttonDown: x=10 y=20 button=1", output)

	def test_reports_x11_start_failure(self):
		source = _SmokeMouseSource(fail=True)
		output = []

		result = runMouseSmoke(environ={"DISPLAY": ":1"}, source=source, write=output.append)

		self.assertEqual(2, result)
		self.assertTrue(source.isStopped)
		self.assertIn("record unavailable", output[-1])


if __name__ == "__main__":
	unittest.main()
