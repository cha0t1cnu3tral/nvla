# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from platform.common.errors import NotSupportedYetError


class LinuxWindowingAdapter:
	@property
	def show_normal(self) -> int:
		raise NotSupportedYetError("Window show mode mapping")

