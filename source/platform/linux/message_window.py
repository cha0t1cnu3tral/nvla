# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from dataclasses import dataclass


class LinuxMessageWindowAdapter:
	def pre_handle_window_message(self, *args, **kwargs):
		return None

	def create_message_window(self, name: str):
		return LinuxMessageWindow(name=name)


@dataclass
class LinuxMessageWindow:
	"""Lifecycle-compatible placeholder until desktop single-instance integration is added."""

	name: str
	isDestroyed: bool = False

	def destroy(self) -> None:
		self.isDestroyed = True
