# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock
import wave

from platform.linux.audio import LinuxAudioAdapter, _generateToneWave


class TestLinuxAudioAdapter(unittest.TestCase):
	def test_prefers_pipewire_player(self):
		adapter = LinuxAudioAdapter(which=lambda executable: f"/usr/bin/{executable}")

		adapter.initialize()

		self.assertTrue(adapter.available)
		self.assertEqual("/usr/bin/pw-play", adapter._executablePath)

	def test_falls_back_to_alsa_player(self):
		adapter = LinuxAudioAdapter(
			which=lambda executable: "/usr/bin/aplay" if executable == "aplay" else None,
		)

		adapter.initialize()

		self.assertEqual("/usr/bin/aplay", adapter._executablePath)

	def test_missing_player_is_non_fatal(self):
		adapter = LinuxAudioAdapter(which=lambda executable: None)

		adapter.initialize()

		self.assertFalse(adapter.available)
		self.assertIsNone(adapter.play_wave_file("/tmp/missing.wav"))
		self.assertIsNone(adapter.beep(440, 20))
		self.assertIsNone(adapter.terminate())

	def test_synchronous_wave_playback_waits_for_command(self):
		process = SimpleNamespace(wait=mock.Mock(), poll=lambda: None)
		popen = mock.Mock(return_value=process)
		adapter = LinuxAudioAdapter(which=lambda executable: "/usr/bin/pw-play", popen=popen)
		adapter.initialize()

		adapter.play_wave_file("/tmp/ready.wav", asynchronous=False)

		self.assertEqual(["/usr/bin/pw-play", "/tmp/ready.wav"], popen.call_args.args[0])
		process.wait.assert_called_once_with()

	def test_terminate_stops_active_commands(self):
		process = SimpleNamespace(wait=mock.Mock(), poll=lambda: None, terminate=mock.Mock())
		adapter = LinuxAudioAdapter(which=lambda executable: "/usr/bin/pw-play", popen=mock.Mock(return_value=process))
		adapter.initialize()
		with mock.patch("platform.linux.audio.threading.Thread") as thread:
			adapter.play_wave_file("/tmp/active.wav")

		adapter.terminate()

		thread.assert_called_once()
		process.terminate.assert_called_once_with()

	def test_failed_tone_command_removes_temporary_wave(self):
		adapter = LinuxAudioAdapter(
			which=lambda executable: "/usr/bin/pw-play",
			popen=mock.Mock(side_effect=OSError("player failed")),
		)
		adapter.initialize()
		with tempfile.TemporaryDirectory() as tempDir:
			with mock.patch("platform.linux.audio.tempfile.tempdir", tempDir):
				with self.assertRaises(OSError):
					adapter.beep(440, 20)

			self.assertEqual([], list(Path(tempDir).iterdir()))

	def test_tone_wave_is_stereo_pcm(self):
		data = _generateToneWave(hz=440, length=20, left=25, right=75)
		with tempfile.TemporaryDirectory() as tempDir:
			path = Path(tempDir) / "tone.wav"
			path.write_bytes(data)
			with wave.open(str(path), "rb") as waveFile:
				self.assertEqual(2, waveFile.getnchannels())
				self.assertEqual(2, waveFile.getsampwidth())
				self.assertEqual(44100, waveFile.getframerate())
				self.assertEqual(882, waveFile.getnframes())


if __name__ == "__main__":
	unittest.main()
