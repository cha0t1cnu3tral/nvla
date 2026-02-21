# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsClipboardAdapter:
	def get_text(self) -> str:
		import api

		return api.getClipData()

	def set_text(self, text: str) -> None:
		import api

		api.copyToClip(text)

