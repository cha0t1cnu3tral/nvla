# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxMessageWindowAdapter:
	def pre_handle_window_message(self, *args, **kwargs):
		raise NotSupportedYetError("Message window pre-handler")

	def create_message_window(self, name: str):
		raise NotSupportedYetError("Message window creation")

