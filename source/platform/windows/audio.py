# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsAudioAdapter:
	def initialize(self) -> None:
		import nvwave

		nvwave.initialize()

	def play_wave_file(self, path: str, asynchronous: bool = True) -> None:
		import nvwave

		nvwave.playWaveFile(path, asynchronous=asynchronous)

	def beep(self, hz: int, length: int, left: int = 50, right: int = 50) -> None:
		import tones

		tones.beep(hz=hz, length=length, left=left, right=right)

	def terminate(self) -> None:
		import nvwave

		nvwave.terminate()
