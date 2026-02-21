# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsMessageWindowAdapter:
	def pre_handle_window_message(self, *args, **kwargs):
		from winAPI.messageWindow import pre_handleWindowMessage

		return pre_handleWindowMessage(*args, **kwargs)

	def create_message_window(self, name: str):
		from winAPI.messageWindow import _MessageWindow

		return _MessageWindow(name)

