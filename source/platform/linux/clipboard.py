# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxClipboardAdapter:
	def get_text(self) -> str:
		raise NotSupportedYetError("Clipboard read")

	def set_text(self, text: str) -> None:
		raise NotSupportedYetError("Clipboard write")

