# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxProcessFocusAdapter:
	def get_desktop_window(self) -> int:
		raise NotSupportedYetError("Desktop window discovery")

	def get_foreground_window(self) -> int:
		raise NotSupportedYetError("Foreground window discovery")

	def list_window_handles(self) -> list[int]:
		raise NotSupportedYetError("Window enumeration")

	def list_process_ids(self) -> list[int]:
		raise NotSupportedYetError("Process enumeration")
