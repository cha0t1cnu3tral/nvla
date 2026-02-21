# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.


class WindowsWindowingAdapter:
	@property
	def show_normal(self) -> int:
		from winUser import SW_SHOWNORMAL

		return SW_SHOWNORMAL

