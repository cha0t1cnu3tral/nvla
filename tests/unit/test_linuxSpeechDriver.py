# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import importlib
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock


class _Action:
	def __init__(self):
		self.calls = []

	def notify(self, **kwargs):
		self.calls.append(kwargs)


class _ImmediateThread:
	def __init__(self, target, args, **kwargs):
		self._target = target
		self._args = args

	def start(self):
		self._target(*self._args)


def _installSynthDriverStubs():
	speech = ModuleType("speech")
	speechCommands = ModuleType("speech.commands")

	class IndexCommand:
		def __init__(self, index):
			self.index = index

	speechCommands.IndexCommand = IndexCommand
	speech.commands = speechCommands
	sys.modules["speech"] = speech
	sys.modules["speech.commands"] = speechCommands

	synthDriverHandler = ModuleType("synthDriverHandler")

	class BaseSynthDriver:
		pass

	class VoiceInfo:
		def __init__(self, id, displayName):
			self.id = id
			self.displayName = displayName

	synthDriverHandler.SynthDriver = BaseSynthDriver
	synthDriverHandler.VoiceInfo = VoiceInfo
	synthDriverHandler.synthDoneSpeaking = _Action()
	synthDriverHandler.synthIndexReached = _Action()
	sys.modules["synthDriverHandler"] = synthDriverHandler
	return speechCommands, synthDriverHandler


speechCommands, synthDriverHandler = _installSynthDriverStubs()
linuxSpeech = importlib.import_module("synthDrivers.linuxSpeech")


class TestLinuxSpeechDriver(unittest.TestCase):
	def setUp(self):
		synthDriverHandler.synthDoneSpeaking.calls.clear()
		synthDriverHandler.synthIndexReached.calls.clear()
		self.process = SimpleNamespace(wait=mock.Mock())
		self.output = SimpleNamespace(
			name="speechDispatcher",
			speak=mock.Mock(return_value=self.process),
			cancel=mock.Mock(),
			terminate=mock.Mock(),
		)

	def _createDriver(self):
		with mock.patch.object(linuxSpeech, "createSpeechOutput", return_value=self.output):
			return linuxSpeech.SynthDriver()

	def test_check_requires_linux_and_available_output(self):
		with (
			mock.patch.object(linuxSpeech.sys, "platform", "linux"),
			mock.patch.object(linuxSpeech, "createSpeechOutput", return_value=self.output),
		):
			self.assertTrue(linuxSpeech.SynthDriver.check())
		with (
			mock.patch.object(linuxSpeech.sys, "platform", "win32"),
			mock.patch.object(linuxSpeech, "createSpeechOutput", return_value=self.output),
		):
			self.assertFalse(linuxSpeech.SynthDriver.check())

	def test_speak_flattens_text_and_notifies_last_index_after_completion(self):
		driver = self._createDriver()

		with mock.patch.object(linuxSpeech, "Thread", _ImmediateThread):
			driver.speak(("active ", speechCommands.IndexCommand(1), "window", speechCommands.IndexCommand(2)))

		self.output.speak.assert_called_once_with("active window")
		self.process.wait.assert_called_once_with()
		self.assertEqual([{"synth": driver, "index": 2}], synthDriverHandler.synthIndexReached.calls)
		self.assertEqual([{"synth": driver}], synthDriverHandler.synthDoneSpeaking.calls)

	def test_cancel_suppresses_stale_completion_notification(self):
		driver = self._createDriver()
		generation = driver._generation

		driver.cancel()
		driver._notifyDone(generation, 1)

		self.output.cancel.assert_called_once_with()
		self.assertEqual([], synthDriverHandler.synthIndexReached.calls)
		self.assertEqual([], synthDriverHandler.synthDoneSpeaking.calls)

	def test_pause_cancels_current_speech(self):
		driver = self._createDriver()

		driver.pause(True)

		self.output.cancel.assert_called_once_with()

	def test_terminate_stops_output(self):
		driver = self._createDriver()

		driver.terminate()

		self.output.terminate.assert_called_once_with()


if __name__ == "__main__":
	unittest.main()
