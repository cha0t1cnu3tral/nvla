# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxAudioAdapter:
	def initialize(self) -> None:
		raise NotSupportedYetError("Audio initialization")

	def play_wave_file(self, path: str, asynchronous: bool = True) -> None:
		raise NotSupportedYetError("Wave playback")

	def beep(self, hz: int, length: int, left: int = 50, right: int = 50) -> None:
		raise NotSupportedYetError("Tone playback")

	def terminate(self) -> None:
		raise NotSupportedYetError("Audio termination")
