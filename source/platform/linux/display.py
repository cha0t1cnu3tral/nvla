# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxDisplayAdapter:
	def set_dpi_awareness(self) -> None:
		raise NotSupportedYetError("DPI awareness setup")

