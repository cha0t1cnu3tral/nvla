# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxInputAdapter:
	def initialize_keyboard(self, observer) -> None:
		raise NotSupportedYetError("Keyboard hook initialization")

	def initialize_mouse(self) -> None:
		raise NotSupportedYetError("Mouse hook initialization")

	def initialize_touch(self) -> None:
		raise NotSupportedYetError("Touch hook initialization")

	def terminate_keyboard(self) -> None:
		raise NotSupportedYetError("Keyboard hook termination")

	def terminate_mouse(self) -> None:
		raise NotSupportedYetError("Mouse hook termination")

	def terminate_touch(self) -> None:
		raise NotSupportedYetError("Touch hook termination")

