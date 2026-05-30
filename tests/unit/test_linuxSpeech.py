# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest
from unittest import mock

from platform.linux.speech import (
	CommandSpeechOutput,
	SpeechCommand,
	createSpeechOutput,
)


class TestLinuxSpeechOutput(unittest.TestCase):
	def test_prefers_speech_dispatcher(self):
		output = createSpeechOutput(
			which=lambda executable: f"/usr/bin/{executable}",
		)

		self.assertIsNotNone(output)
		self.assertEqual("speechDispatcher", output.name)
		self.assertEqual("/usr/bin/spd-say", output.executablePath)

	def test_falls_back_to_espeak_ng(self):
		output = createSpeechOutput(
			which=lambda executable: "/usr/bin/espeak-ng" if executable == "espeak-ng" else None,
		)

		self.assertIsNotNone(output)
		self.assertEqual("espeakNg", output.name)

	def test_returns_none_without_supported_command(self):
		self.assertIsNone(createSpeechOutput(which=lambda executable: None))

	def test_speech_dispatcher_waits_for_completion(self):
		process = SimpleNamespace(poll=lambda: None)
		popen = mock.Mock(return_value=process)
		output = createSpeechOutput(
			which=lambda executable: "/usr/bin/spd-say" if executable == "spd-say" else None,
			popen=popen,
		)

		self.assertEqual(process, output.speak("active window title"))
		popen.assert_called_once()
		self.assertEqual(
			["/usr/bin/spd-say", "--wait", "active window title"],
			popen.call_args.args[0],
		)

	def test_cancel_terminates_process_and_cancels_speech_dispatcher_queue(self):
		process = SimpleNamespace(poll=lambda: None, terminate=mock.Mock())
		run = mock.Mock()
		output = createSpeechOutput(
			which=lambda executable: "/usr/bin/spd-say" if executable == "spd-say" else None,
			popen=mock.Mock(return_value=process),
			run=run,
		)

		output.speak("first")
		output.cancel()

		process.terminate.assert_called_once_with()
		self.assertEqual(["/usr/bin/spd-say", "--cancel"], run.call_args.args[0])

	def test_espeak_cancel_does_not_launch_cancel_command(self):
		process = SimpleNamespace(poll=lambda: None, terminate=mock.Mock())
		run = mock.Mock()
		output = createSpeechOutput(
			which=lambda executable: "/usr/bin/espeak-ng" if executable == "espeak-ng" else None,
			popen=mock.Mock(return_value=process),
			run=run,
		)

		output.speak("first")
		output.cancel()

		process.terminate.assert_called_once_with()
		run.assert_not_called()

	def test_discards_completed_processes_before_speaking(self):
		finished = SimpleNamespace(poll=lambda: 0, terminate=mock.Mock())
		active = SimpleNamespace(poll=lambda: None, terminate=mock.Mock())
		popen = mock.Mock(side_effect=(finished, active))
		output = CommandSpeechOutput(
			command=SpeechCommand(name="test", executable="test"),
			executablePath="/usr/bin/test",
			popen=popen,
		)

		output.speak("first")
		output.speak("second")
		output.cancel()

		finished.terminate.assert_not_called()
		active.terminate.assert_called_once_with()


if __name__ == "__main__":
	unittest.main()
