# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxSessionAdapter:
	def initialize(self) -> None:
		raise NotSupportedYetError("Session tracking initialization")

	def pump_all(self) -> None:
		raise NotSupportedYetError("Session tracking pump")

