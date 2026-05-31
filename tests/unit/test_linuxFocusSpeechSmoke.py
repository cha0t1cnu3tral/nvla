# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

import controlTypes
from platform.linux.focus_speech_smoke import runFocusSpeechSmoke


class _SmokeBackend:
	def __init__(self, *, fail=False):
		self.fail = fail
		self.listener = None
		self.isTerminated = False

	def registerEventListener(self, listener):
		self.listener = listener

	def initialize(self):
		if self.fail:
			raise RuntimeError("registry unavailable")

	def pump_all(self):
		if self.listener is None:
			return
		listener = self.listener
		self.listener = None
		listener(
			SimpleNamespace(
				kind="focus",
				isFocused=True,
				sourceName="Save",
				sourceDescription="Write changes",
				role=controlTypes.Role.BUTTON,
			),
		)

	def terminate(self):
		self.isTerminated = True


class _SmokeSpeechOutput:
	name = "testSpeech"

	def __init__(self):
		self.spoken = []
		self.cancelCount = 0
		self.isTerminated = False

	def speak(self, text):
		self.spoken.append(text)

	def cancel(self):
		self.cancelCount += 1

	def terminate(self):
		self.isTerminated = True


class TestLinuxFocusSpeechSmoke(unittest.TestCase):
	def test_speaks_focused_atspi_objects_and_cleans_up(self):
		backend = _SmokeBackend()
		output = _SmokeSpeechOutput()
		writes = []

		result = runFocusSpeechSmoke(
			durationSeconds=0,
			backend=backend,
			speechOutput=output,
			write=writes.append,
		)

		self.assertEqual(0, result)
		self.assertEqual(
			["AT SPI focus speech smoke started", "Save, Write changes, button"],
			output.spoken,
		)
		self.assertEqual(1, output.cancelCount)
		self.assertTrue(backend.isTerminated)
		self.assertTrue(output.isTerminated)
		self.assertIn("focus: Save, Write changes, button", writes)

	def test_reports_missing_speech_output(self):
		writes = []

		result = runFocusSpeechSmoke(createOutput=lambda: None, write=writes.append)

		self.assertEqual(1, result)
		self.assertIn("Speech Dispatcher", writes[0])

	def test_reports_atspi_initialization_failure_and_cleans_up(self):
		backend = _SmokeBackend(fail=True)
		output = _SmokeSpeechOutput()
		writes = []

		result = runFocusSpeechSmoke(backend=backend, speechOutput=output, write=writes.append)

		self.assertEqual(2, result)
		self.assertTrue(backend.isTerminated)
		self.assertTrue(output.isTerminated)
		self.assertIn("registry unavailable", writes[0])


if __name__ == "__main__":
	unittest.main()
